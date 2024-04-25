# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

from unittest.mock import call
from src.backend_sidecar import bulk_upload, bulk_download

def test_bulk_upload(tmpdir, mocker):
    files_to_upload = []
    for filename in ["unittest1.txt", "unittest2.txt"]:
        filepath = os.path.join(tmpdir, filename)
        files_to_upload.append(filepath)
        with open(filepath, 'w') as f:
            f.write("content")

    mock_upload = mocker.patch('src.backend_sidecar.rest_client.upload_prepared_doc', return_value=None)
    response = bulk_upload(tmpdir)
    
    mock_upload.assert_has_calls([call(filepath) for filepath in files_to_upload], any_order=True)
    assert len(os.listdir(tmpdir)) == 0
