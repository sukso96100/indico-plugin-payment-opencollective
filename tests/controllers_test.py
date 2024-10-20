# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2024 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from unittest.mock import MagicMock

import pytest
from indico.modules.events.payment.models.transactions import PaymentTransaction

from indico_payment_opencollective.controllers import RHOpenCollectivePostPaymentCallback
from indico_payment_opencollective.plugin import OpenCollectivePaymentPlugin
from tests.constants import GQL_QUERY_RESULT_MOCK, GQL_QUERY_RESULT_MOCK_1, GQL_QUERY_RESULT_MOCK_2


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('gql_mock_data', 'expected'), (
    (GQL_QUERY_RESULT_MOCK, True),
    (GQL_QUERY_RESULT_MOCK_1, False),
    (GQL_QUERY_RESULT_MOCK_2, False),
))
def test_oc_verify_amount(mocker, gql_mock_data, expected):
    nai = mocker.patch('indico_payment_opencollective.controllers.notify_amount_inconsistency')
    mock_client = MagicMock()
    mock_client.execute.return_value = gql_mock_data
    mocker.patch('gql.Client', return_value=mock_client)
    rh = RHOpenCollectivePostPaymentCallback()
    rh.event = MagicMock(id=1)
    rh.registration = MagicMock()
    rh.registration.price = GQL_QUERY_RESULT_MOCK['order']['amount']['value']
    rh.registration.currency = GQL_QUERY_RESULT_MOCK['order']['amount']['currency']
    with OpenCollectivePaymentPlugin.instance.plugin_context():
        assert rh._verify_amount(gql_mock_data) == expected
        assert nai.called == (not expected)

@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('gql_mock_data', 'expected'), (
    (GQL_QUERY_RESULT_MOCK, True),
    (GQL_QUERY_RESULT_MOCK_1, False),
))
def test_oc_is_transaction_duplicated(mocker, gql_mock_data, expected):
    mock_client = MagicMock()
    mock_client.execute.return_value = gql_mock_data
    mocker.patch('gql.Client', return_value=mock_client)
    rh = RHOpenCollectivePostPaymentCallback()
    rh.registration = MagicMock()
    rh.registration.transaction = None
    assert not rh._is_transaction_duplicated(gql_mock_data)
    transaction = PaymentTransaction(provider='opencollective', data=GQL_QUERY_RESULT_MOCK)
    rh.registration.transaction = transaction
    assert rh._is_transaction_duplicated(gql_mock_data) == expected