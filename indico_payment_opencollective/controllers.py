# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2024 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from itertools import chain

import requests
from flask import flash, redirect, request
from flask_pluginengine import current_plugin
from werkzeug.exceptions import BadRequest

from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.notifications import notify_amount_inconsistency
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration.models.registrations import Registration
from indico.web.flask.util import url_for
from indico.web.rh import RH

from indico_payment_opencollective import _


IPN_VERIFY_EXTRA_PARAMS = (('cmd', '_notify-validate'),)
OC_API_BASEURL = "https://api.opencollective.com"

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
        if not self.registration:
            raise BadRequest

    def _process(self):
        oc_transactionid = request.args.get('transactionid') 
        slug = current_plugin.settings.get('event_slug')
        if not slug:
            slug = current_plugin.settings.get('collective_slug')
        oc_tx_response = requests.get(f"{OC_API_BASEURL}/v1/collectives/{slug}/transactions/{oc_transactionid}")
        oc_tx_result = oc_tx_response.json()
        oc_tx_amount = oc_tx_result['result']['amount'] / 100
        oc_tx_currency = oc_tx_result['result']['currency']
        oc_tx_order_status = oc_tx_result['result']['order']['status']
        oc_tx_payee_slug = oc_tx_result['result']['collective']['slug']

        # Check if amount paid to correct collective
        if slug != oc_tx_payee_slug:
            current_plugin.logger.warning(f"Payment made to wrong collective (Expected: {slug}, Actual: {oc_tx_payee_slug})")
            return
        self._verify_amount(oc_tx_result)
        register_transaction(registration=self.registration,
                             amount=float(oc_tx_amount),
                             currency=oc_tx_currency,
                             action=oc_tx_order_status_action_mapping[oc_tx_order_status],
                             provider='opencollective',
                             data=oc_tx_result)
        flash(_('Your payment request has been processed.'), 'success')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))


    def _verify_amount(self, oc_tx_result: dict):
        expected_amount = self.registration.price
        expected_currency = self.registration.currency
        amount = oc_tx_result['result']['amount'] / 100
        currency = oc_tx_result['result']['currency	']
        if expected_amount == amount and expected_currency == currency:
            return True
        current_plugin.logger.warning("Payment doesn't match event's fee: %s %s != %s %s",
                                      amount, currency, expected_amount, expected_currency)
        notify_amount_inconsistency(self.registration, amount, currency)
        return False


