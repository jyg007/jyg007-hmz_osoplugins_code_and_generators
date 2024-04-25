# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
from src import frontend_sidecar

sample_json = [
    {
        "id": "filename1",
        "content": "content1",
    },
    {
        "id": "filename2",
        "content": "content2",
    }
]
# Bulk_download


def test_bulk_download(mocker):
    mocker.patch("src.dbaas_client.dap_resource.dbaas.dequeue_all",
                 return_value=sample_json)
    mocker.patch("src.dbaas_client.dap_resource.DAPDBaaSResource")
    response_dir = frontend_sidecar.bulk_download()
    print('Response of bulk_download', response_dir)
    count_of_files = 0
    for filename in os.listdir(response_dir):
        count_of_files += 1
        filepath = os.path.join(response_dir, filename)
        os.remove(filepath)
    assert count_of_files == 2


def test_dequeue_all(mocker):
    mocker.patch(
        "src.dbaas_client.dap_resource.dbaas.dequeue_all", return_value=[])
    mocker.patch("src.dbaas_client.dap_resource.DAPDBaaSResource")
    response_dir = frontend_sidecar.bulk_download()
    print('Response of response_dir', response_dir)
    count_of_files = 0
    for filename in os.listdir(response_dir):
        count_of_files += 1
        filepath = os.path.join(response_dir, filename)
        os.remove(filepath)
    assert count_of_files == 0

# Bulk_upload


def test_bulk_upload(mocker):
    dbaas_client_mock = mocker.patch("src.frontend_sidecar.DBaaSClient")
    mocker.patch("src.frontend_sidecar.os.listdir")
    frontend_sidecar.bulk_upload()
    dbaas_client_mock.assert_called_once_with()
