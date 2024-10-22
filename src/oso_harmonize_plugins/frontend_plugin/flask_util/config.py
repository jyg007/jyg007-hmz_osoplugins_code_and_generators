# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import oso_harmonize_plugins.frontend_plugin.consts as consts

class BaseConfig(object):
    app_name = "frontend_plugin"
    root_path = consts.FLASK_ROOT_PATH
   
class SignedConfig(BaseConfig):
    app_name = "frontend_plugin"
    PREPARED_DIR = consts.PREPARED_DIR
    SIGNED_DIR = consts.SIGNED_DIR
