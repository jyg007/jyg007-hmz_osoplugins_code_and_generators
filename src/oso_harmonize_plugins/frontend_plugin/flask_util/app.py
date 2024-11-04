#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

from flask import Flask
from flask_restx import Api

from oso_harmonize_plugins.common import pre_request

from .config import BaseConfig


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
    configure_frontend_plugin_manager(app)

    return app


def configure_app(app: Flask, config: object):
    app.config.from_object(config)


def configure_api(app: Flask):
    from ..api.v1alpha1 import api as v1alpha1

    api = Api(
        title="My Title",
        version="1.0",
        description="A description",
        # All API metadatas
    )

    api.add_namespace(v1alpha1, path="/api/frontend/" + v1alpha1.name)
    api.init_app(app)


def configure_logging(app: Flask):
    return


def configure_frontend_plugin_manager(app: Flask):
    from oso_harmonize_plugins.frontend_plugin.frontend_plugin_manager import (
        FrontendPluginManager,
    )

    app.fpm = FrontendPluginManager()
