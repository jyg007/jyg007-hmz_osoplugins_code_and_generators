# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import requests
import unittest

component_cert = "-----BEGIN%20CERTIFICATE-----%0AMIICqzCCAZOgAwIBAgIURUiTTJYKjX4SIN0gMNOSJ%2BHaK2QwDQYJKoZIhvcNAQEL%0ABQAwCzEJMAcGA1UEAwwAMB4XDTIzMTEwMzE2MzA0OVoXDTI0MTEwMjE2MzA0OVow%0AFDESMBAGA1UEAwwJQ09NUE9ORU5UMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB%0ACgKCAQEApnfHhVjwgaOWPLOLPqtwDQ2Qw8DltrlR/0GHkfjjGrHiKjrxfA7aJPdh%0AOgDizFQfzjDtpZiyLx6sxFKoAeLMgWELNdI3Kg2YrgxmYc6rmJAxnaGchdo0cUTM%0AkhpAirvSEpPthwBuSsmhrJWGZq42VUASN0x4LwCPeTxiU45VP%2By4B4I4cSExapCa%0A74BynH7KjI%2B0XS3nLc7Vhxq9y9XQx1dxxt7K/Xxo3pueY6rJ40M9X7lYI07AicFz%0A5VM7dEuM8r8lLGYn/3AWTbGmuYO7sedFfnNDM4bS2ak9X1ggWwfK0EgZGX3w8L/8%0Al%2BtKR5Q0%2BBos8ZRF5JIxxQ%2BOuUx3EwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQCV%0A1ceRRdB1H7UaTTLitzFYmDJSSWYr3DInYezTO9l1uUufnyZnywYOmYEzp9rXXnoI%0A9wM5c25vfcHsrjujLPo8aFNmlq/DwgLomPgbcMqBxrsHTBYSSZz864J/JUiDz6JU%0ApJ8BLDP0pGPxk53bU7lHLxmsXtuVj5mOTk18VtIgoolqXAasNHYrsKHvpbx%2BgZLo%0A828fJrTxp9mQgzDQm4//UE%2Btg0VO9FKqq0FwX50LSXWXwT/yyDAayyf9OBTPMEmJ%0AFyzITeKOOgH8lY8Xrg2owi%2Bn1UPy6/PYElZThyZ%2Bjv%2B58bGx0ac8g3Z%2BZnQWh6lr%0AFCFuZ66kyJic666HooSx%0A-----END%20CERTIFICATE-----%0A"


def test_bulk_download(client, mocker, mock_session_get):
    mock_session_get.side_effect = [
        mocker.Mock(headers={'Content-Disposition': True}, content=b'test1'),
        mocker.Mock(headers={'Content-Disposition': True}, content=b'test2'),
        mocker.Mock(headers={}, content=None),
    ]
    mocker.patch("uuid.uuid4", side_effect=["file1", "file2"])

    response = client.get("api/backend/v1alpha1/documents",
                          headers={
                              'X-SSL-CERT': component_cert,
                              'X-SSL-CLIENT-VERIFY': 'SUCCESS',
                          }).json

    assert response == {
        'documents': [
            {'id': 'file1', 'content': 'test1'},
            {'id': 'file2', 'content': 'test2'},
        ],
        'count': 2
    }


def test_bulk_upload(client, mocker, mock_session_post):
    res_obj = mocker.Mock("requests.Response")

    mock_session_post.return_value = res_obj

    documents = [
        {"id": "file3", "content": "test"},
        {"id": "file4", "content": "test"},
    ]

    data = {
        "documents":  documents,
        "count": len(documents)
    }
    response = client.post('api/backend/v1alpha1/documents',
                           headers={
                               'X-SSL-CERT': component_cert,
                               'X-SSL-CLIENT-VERIFY': 'SUCCESS',
                           },  json=data).json

    assert response == 'OK'


def test_status(client, mocker, mock_session_get):
    res_obj = mocker.Mock('requests.Response')
    mock_session_get.return_value = res_obj

    response = client.get('api/backend/v1alpha1/status',
                          headers={
                              'X-SSL-CERT': component_cert,
                              'X-SSL-CLIENT-VERIFY': 'SUCCESS',
                          })
    assert response.status_code == 200
    assert response.json == {'status': 'OK'}


def test_status_timeout(client, mocker, mock_session_get):
    mock_session_get.side_effect = requests.exceptions.HTTPError

    response = client.get('api/backend/v1alpha1/status',
                          headers={
                              'X-SSL-CERT': component_cert,
                              'X-SSL-CLIENT-VERIFY': 'SUCCESS',
                          })
    assert response.status_code == 503
