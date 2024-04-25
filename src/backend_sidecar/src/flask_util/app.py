# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

from flask import Flask
from flask_restx import Api
from flask_util.config import BaseConfig

from . import pre_request


def create_app(config: object, app_name=None, root_path=None):

    if app_name is None:
        if config is None:
            app_name = BaseConfig.app_name
        elif config.app_name is not None:
            app_name = config.app_name
        else:
            app_name = BaseConfig.app_name

    if root_path is None:
        if config is None:
            root_path = BaseConfig.root_path
        elif config.root_path is not None:
            root_path = config.root_path
        else:
            root_path = BaseConfig.root_path

    app = Flask(__name__, instance_relative_config=True)

    configure_app(app, config)
    pre_request.configure_flask_common(app)
    configure_api(app)
    configure_logging(app)

    return app


def configure_app(app: Flask, config: object):
    app.config.from_object(config)


def configure_api(app: Flask):
    from api.v1alpha1 import api as v1alpha1
    api = Api(
        title='My Title',
        version='1.0',
        description='A description',
    )

    api.add_namespace(v1alpha1, path='/api/backend/' + v1alpha1.name)
    api.init_app(app)


def configure_logging(app: Flask):
    return
