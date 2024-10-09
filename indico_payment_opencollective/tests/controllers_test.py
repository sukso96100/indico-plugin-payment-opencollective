# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2024 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from unittest.mock import MagicMock

import pytest

from indico_payment_opencollective.controllers import RHOpenCollectivePostPaymentCallback
from indico_payment_opencollective.plugin import OpenCollectivePaymentPlugin
from indico_payment_opencollective.tests.constants import GQL_QUERY_RESULT_MOCK


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('amount', 'currency', 'expected'), (
    ('10', 'USD', True),
    ('20', 'USD', False),
    ('10', 'EUR', False),
))
def test_oc_verify_amount(mocker, amount, currency, expected):
    nai = mocker.patch('indico_payment_opencollective.controllers.notify_amount_inconsistency')
    gqlmock = mocker.patch('gql.Client.execute', return_value=GQL_QUERY_RESULT_MOCK)
    rh = RHOpenCollectivePostPaymentCallback()
    rh.event = MagicMock(id=1)
    rh.registration = MagicMock()
    rh.registration.price = amount
    rh.registration.currency = currency
    with OpenCollectivePaymentPlugin.instance.plugin_context():
        assert gqlmock.called == True
        assert rh._verify_amount() == expected
        assert nai.called == (not expected)

