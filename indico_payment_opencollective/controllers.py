# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2024 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from flask import flash, redirect, request
from flask_pluginengine import current_plugin
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.notifications import \
    notify_amount_inconsistency
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration.models.registrations import \
    Registration
from indico.web.flask.util import url_for
from indico.web.rh import RH
from werkzeug.exceptions import BadRequest

from indico_payment_opencollective import _
from indico_payment_opencollective.constants import (OC_API_BASEURL,
                                                     OC_GQL_ORDER_QUERY)

oc_tx_order_status_action_mapping = {'PAID': TransactionAction.complete,
                                     'REJECTED': TransactionAction.reject,
                                     'PENDING': TransactionAction.pending,
                                     'CANCELLED': TransactionAction.cancel}


class RHOpenCollectivePostPaymentCallback(RH):
    """Process the redirects after payment on Open Collective"""

    CSRF_ENABLED = False

    def _process_args(self):
        self.token = request.args['token']
        self.registration = Registration.query.filter_by(uuid=self.token).first()
        self.oc_order_id = request.args['orderId']
        self.oc_order_id_v2 = request.args['orderIdV2'] 
        self.oc_order_status = request.args['status'] 
        if not self.registration:
            raise BadRequest

    def _process(self):
        oc_token = slug = self._get_event_settings('token')
        slug = self._get_event_settings('event_slug')
        if not slug:
            slug = self._get_event_settings('collective_slug')

        transport = RequestsHTTPTransport(
            url=OC_API_BASEURL,
            verify=True,
            retries=3,
            headers={'Personal-Token': oc_token}
        )

        client = Client(transport=transport, fetch_schema_from_transport=True)
        gql_query = gql(OC_GQL_ORDER_QUERY)
        gql_params = {
            "order": {
                "id": self.oc_order_id_v2,
                "legacyId": int(self.oc_order_id)
                }
            }
        oc_order_result = client.execute(gql_query, variable_values=gql_params)
        oc_order_amount = oc_order_result['order']['amount']['value']
        oc_order_currency = oc_order_result['order']['amount']['currency']
        oc_order_order_status = oc_order_result['order']['status']
        oc_order_payee_slug = oc_order_result['order']['toAccount']['slug']
        oc_order_payment_frequency = oc_order_result['order']['frequency']

        is_payment_valid = True
        invalid_error_msgs = []

        if self._is_transaction_duplicated(oc_order_result):
            error_msg = "Payment not recorded because transaction was duplicated"
            current_plugin.logger.info(f"{error_msg}\nData received {oc_order_result}")
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        if slug != oc_order_payee_slug:
            error_msg = f"Payment made to wrong collective (Expected: {slug}, Actual: {oc_order_payee_slug})"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        if oc_order_payment_frequency != "ONETIME":
            error_msg = f"Payment must be ONETIME (Expected: ONETIME, Actual: {oc_order_payment_frequency})"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        if self.oc_order_status != oc_order_order_status:
            current_plugin.logger.warning(
                f"Payment status from callback url and graphql response not matches. \
                    This could be due to update on order after callback data received from url \
                        (From URL: {self.oc_order_status}, From GraphQL Response: {oc_order_order_status})")
            
        if oc_order_order_status == "REJECTED":
            error_msg = "Payment has been rejected on Open Collective"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        elif oc_order_order_status == "CANCELED":
            error_msg = "Payment has been canceled on Open Collective"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        elif oc_order_order_status == "ERROR":
            error_msg = "An error occurred while Open Collective is processing your payment"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False
        elif oc_order_order_status == "REFUNDED":
            error_msg = "Payment has been refunded on Open Collective"
            current_plugin.logger.warning(error_msg)
            invalid_error_msgs.append(error_msg)
            is_payment_valid = False

        if is_payment_valid:
            is_amount_valid = self._verify_amount(oc_order_result)
            register_transaction(registration=self.registration,
                                amount=float(oc_order_amount),
                                currency=oc_order_currency,
                                action=oc_tx_order_status_action_mapping[oc_order_order_status],
                                provider='opencollective',
                                data=oc_order_result)
            if is_amount_valid:
                flash(_('Your payment request has been processed.'), 'success')
            else:
                flash(_('Your payment request has been processed. But paid amount not matches. \
                        Please contact organizers to check and resolve this issue.'), 'warning')
        else:
            warning_msg = 'Your payment request is not valid. Thus, not recorded for this registration. \
                Please contact organizers to check and resolve this issue.<br/>'
            for msg_item in invalid_error_msgs:
                warning_msg = f"{warning_msg}<br/>{msg_item}"
            flash(_(warning_msg), 'error')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))
    
    def _is_transaction_duplicated(self, order_data: dict):
        transaction = self.registration.transaction
        if not transaction or transaction.provider != 'opencollective':
            return False
        return (transaction.data['order']['status'] == order_data['order']['status'] and
                transaction.data['order']['id'] == order_data['order']['id'] and 
                transaction.data['order']['legacyId'] == order_data['order']['legacyId'])

    def _verify_amount(self, oc_order_result: dict):
        expected_amount = self.registration.price
        expected_currency = self.registration.currency
        amount = oc_order_result['order']['amount']['value']
        currency = oc_order_result['order']['amount']['currency']
        if expected_amount == amount and expected_currency == currency:
            return True
        current_plugin.logger.warning("Payment doesn't match event's fee: %s %s != %s %s",
                                      amount, currency, expected_amount, expected_currency)
        notify_amount_inconsistency(self.registration, amount, currency)
        return False

    def _get_event_settings(self, settings_key: str):
        return current_plugin.event_settings.get(self.registration.registration_form.event, settings_key)
