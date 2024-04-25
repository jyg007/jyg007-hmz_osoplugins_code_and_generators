# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pytest
import requests

from src.flask_util.app import create_app
from src.flask_util.config import BaseConfig

env = {
    "COMPONENT_FINGERPRINTS": "2874175a37463fcbdb77f063626ef1b0b62578c9",
}


@pytest.fixture
def set_env():
    for k, v in env.items():
        os.environ[k] = v


@pytest.fixture
def mock_session_get(mocker):
    mock_session_get = mocker.patch.object(
        requests.Session, 'get', auto_spec=True)
    return mock_session_get


@pytest.fixture
def mock_session_post(mocker):
    mock_session_post = mocker.patch.object(
        requests.Session, 'post', auto_spec=True)
    return mock_session_post


@pytest.fixture
def app(set_env, tmpdir, mocker, monkeypatch):
    monkeypatch.setenv('BACKEND_ENDPOINT', 'http://localhost/')

    config = BaseConfig()
    config.TESTING = True
    config.PREPARED_DIR = os.path.join(tmpdir, 'prepared')
    config.SIGNED_DIR = os.path.join(tmpdir, 'signed')

    app = create_app(config=config)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
