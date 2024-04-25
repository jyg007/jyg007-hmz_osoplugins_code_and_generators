#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

terraform init
terraform destroy -auto-approve
terraform apply -auto-approve
