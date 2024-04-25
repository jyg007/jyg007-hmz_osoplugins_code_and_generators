# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

locals {
  auths = {
    (var.REGISTRY_URL) : {
      "username": var.REGISTRY_USERNAME,
      "password": var.REGISTRY_PASSWORD,
      "insecure": var.REGISTRY_INSECURE
    }
  }
  workload_template = {
    "type" : "workload",
    "auths": local.auths,
    "images": {}
  }
}
