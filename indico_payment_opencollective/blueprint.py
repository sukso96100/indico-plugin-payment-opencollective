# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2024 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from indico.core.plugins import IndicoPluginBlueprint

from indico_payment_opencollective.controllers import RHOpenCollectivePostPaymentRedirect, RHOpenCollectiveCancel, RHOpenCollectiveSuccess


blueprint = IndicoPluginBlueprint(
    'payment_opencollective', __name__,
    url_prefix='/event/<int:event_id>/registrations/<int:reg_form_id>/payment/response/opencollective'
)

blueprint.add_url_rule('/cancel', 'cancel', RHOpenCollectiveCancel, methods=('GET', 'POST'))
blueprint.add_url_rule('/success', 'success', RHOpenCollectiveSuccess, methods=('GET', 'POST'))
