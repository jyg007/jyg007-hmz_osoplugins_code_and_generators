# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from src.flask_util.app import create_app
from src.flask_util.config import SignedConfig
import os


env = {
    "COMPONENT_FINGERPRINTS": "2874175a37463fcbdb77f063626ef1b0b62578c9",
}


@pytest.fixture
def set_env():
    for k, v in env.items():
        os.environ[k] = v


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


@pytest.fixture
def app(set_env, tmpdir, mocker):
    mocker.patch("src.dbaas_client.dap_resource.DAPDBaaSResource")
    mocker.patch("src.dbaas_client.dap_resource.dbaas.dequeue_all",
                 return_value=sample_json)
    mocker.patch("src.dbaas_client.dbaas.enqueue")
    config = SignedConfig()
    config.TESTING = True
    config.PREPARED_DIR = os.path.join(tmpdir, "/frontend-sidecar/prepared")
    config.SIGNED_DIR = os.path.join(tmpdir, "/frontend-sidecar/signed")

    app = create_app(config=config)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
