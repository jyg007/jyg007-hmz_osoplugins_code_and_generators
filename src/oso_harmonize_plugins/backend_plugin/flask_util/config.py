# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import oso_harmonize_plugins.frontend_plugin.consts as consts

class BaseConfig(object):
    app_name = "backend_plugin"
    root_path = consts.FLASK_ROOT_PATH
    
class BackendConfig(BaseConfig):
    app_name = "backend_plugin"
    PREPARED_DIR=consts.PREPARED_DIR
    SIGNED_DIR=consts.SIGNED_DIR
   
