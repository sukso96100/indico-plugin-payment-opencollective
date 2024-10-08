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
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.notifications import notify_amount_inconsistency
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration.models.registrations import Registration
from indico.web.flask.util import url_for
from indico.web.rh import RH

from indico_payment_opencollective import _


IPN_VERIFY_EXTRA_PARAMS = (('cmd', '_notify-validate'),)
OC_API_BASEURL = "https://api.opencollective.com/graphql/v2"
OC_GQL_ORDER_QUERY = """
query (
  $order: OrderReferenceInput!
) {
  order(order: $order) {
    id
    legacyId
    description
    amount {
      value
      currency
      valueInCents
    }
    taxAmount {
      value
      currency
      valueInCents
    }
    totalAmount {
      value
      currency
      valueInCents
    }
    quantity
    status
    frequency
    nextChargeDate
    fromAccount {
      id
      slug
      type
      name
      legalName
      description
      longDescription
      tags
      currency
      expensePolicy
      isIncognito
      createdAt
      updatedAt
      isArchived
      isFrozen
      isActive
      isHost
      isAdmin
      emails
      supportedExpenseTypes
      categories
    }
    toAccount {
      id
      slug
      type
      name
      legalName
      description
      longDescription
      tags
      currency
      expensePolicy
      isIncognito
      createdAt
      updatedAt
      isArchived
      isFrozen
      isActive
      isHost
      isAdmin
      emails
      supportedExpenseTypes
      categories
    }
    transactions {
      id
      legacyId
      group
      type
      kind
      description
      hostCurrencyFxRate
      createdAt
      updatedAt
      isRefunded
      isRefund
      isDisputed
      isInReview
      isOrderRejected
      merchantId
      invoiceTemplate
    }
    createdAt
    updatedAt
    totalDonations {
      value
      currency
      valueInCents
    }
    paymentMethod {
      id
      legacyId
      name
      service
      type
      data
      expiryDate
      createdAt
    }
    hostFeePercent
    platformTipAmount {
      value
      currency
      valueInCents
    }
    platformTipEligible
    tags
    tax {
      id
      type
      rate
      idNumber
    }
    tax {
      type
      rate
    }
    activities {
      offset
      limit
      totalCount
    }
    data
    customData
    memo
    createdByAccount {
      id
      slug
      type
      name
      legalName
      description
      longDescription
      tags
      currency
      expensePolicy
      isIncognito
      createdAt
      updatedAt
      isArchived
      isFrozen
      isActive
      isHost
      isAdmin
      emails
      supportedExpenseTypes
      categories
    }
    processedAt
    pendingContributionData {
      expectedAt
      paymentMethod
      ponumber
      memo
    }
    needsConfirmation
    comments{
      offset
      limit
      totalCount
    }
  }
}

"""

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
        oc_order_id = request.args.get('orderId') 
        oc_order_id_v2 = request.args.get('orderIdV2') 
        oc_status = request.args.get('status')
        slug = current_plugin.settings.get('event_slug')
        if not slug:
            slug = current_plugin.settings.get('collective_slug')

        transport = RequestsHTTPTransport(
            url=OC_API_BASEURL,
            verify=True,
            retries=3,
        )

        client = Client(transport=transport, fetch_schema_from_transport=True)
        gql_query = gql(OC_GQL_ORDER_QUERY)
        gql_params = {
            "order": {
                "id": oc_order_id_v2,
                "legacyId": int(oc_order_id)
                }
            }
        oc_order_result = client.execute(gql_query, variable_values=gql_params)
        oc_order_amount = oc_order_result['data']['order']['amount']['value']
        oc_order_currency = oc_order_result['data']['order']['amount']['currency']
        oc_order_order_status = oc_order_result['data']['order']['status']
        oc_order_payee_slug = oc_order_result['data']['order']['toAccount']['slug']

        # Check if amount paid to correct collective
        if slug != oc_order_payee_slug:
            current_plugin.logger.warning(f"Payment made to wrong collective (Expected: {slug}, Actual: {oc_order_payee_slug})")
            return
        if oc_status != oc_order_order_status:
            current_plugin.logger.warning(
                f"Payment status from callback url and graphql response not matches. This could be due to update on order after callback data received from url (From URL: {oc_status}, From GraphQL Response: {oc_order_order_status})")
        self._verify_amount(oc_order_result)
        register_transaction(registration=self.registration,
                             amount=float(oc_order_amount),
                             currency=oc_order_currency,
                             action=oc_tx_order_status_action_mapping[oc_order_order_status],
                             provider='opencollective',
                             data=oc_order_result)
        flash(_('Your payment request has been processed.'), 'success')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))


    def _verify_amount(self, oc_order_result: dict):
        expected_amount = self.registration.price
        expected_currency = self.registration.currency
        amount = oc_order_result['data']['order']['amount']['value']
        currency = oc_order_result['data']['order']['amount']['currency']
        if expected_amount == amount and expected_currency == currency:
            return True
        current_plugin.logger.warning("Payment doesn't match event's fee: %s %s != %s %s",
                                      amount, currency, expected_amount, expected_currency)
        notify_amount_inconsistency(self.registration, amount, currency)
        return False


