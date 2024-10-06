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

paypal_transaction_action_mapping = {'Completed': TransactionAction.complete,
                                     'Denied': TransactionAction.reject,
                                     'Pending': TransactionAction.pending}


class RHOpenCollectivePostPaymentRedirect(RH):
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
      
        # current_plugin.logger.warning("Payment status '%s' not recognized\nData received: %s",
                                        #   payment_status, request.form)
            # return
        self._verify_amount(oc_tx_result)
        register_transaction(registration=self.registration,
                             amount=float(request.form['mc_gross']),
                             currency=request.form['mc_currency'],
                             action=paypal_transaction_action_mapping[payment_status],
                             provider='opencollective',
                             data=request.form)


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


class RHOpenCollectiveSuccess(RHOpenCollectivePostPaymentRedirect):
    """Confirmation message after successful payment"""

    def _process(self):
        flash(_('Your payment request has been processed.'), 'success')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))


class RHOpenCollectiveCancel(RHOpenCollectivePostPaymentRedirect):
    """Cancellation message"""

    def _process(self):
        flash(_('You cancelled the payment process.'), 'info')
        return redirect(url_for('event_registration.display_regform', self.registration.locator.registrant))
