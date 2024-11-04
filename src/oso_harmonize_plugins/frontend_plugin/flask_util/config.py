#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import oso_harmonize_plugins.frontend_plugin.consts as consts


class BaseConfig(object):
    app_name = "frontend_plugin"
    root_path = consts.FLASK_ROOT_PATH


class SignedConfig(BaseConfig):
    app_name = "frontend_plugin"
