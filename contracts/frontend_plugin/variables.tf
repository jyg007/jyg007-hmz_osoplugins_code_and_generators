# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "FRONTEND_PLUGIN_IMAGE" {
  type        = string
  description = "Frontend plugin image name"
}

# Harmonize
variable "SK" {
  type = string
  description = "Private (secret) key of a registered user used to login to Harmonize"
}

variable "PUB" {
  type = string
  description = "Public key of a registered user used to login to Harmonize"
}

variable "VAULT_ID" {
  type = string
  description = "Harmonize vault id"
}

variable "HMZ_SERVER" {
  type = string
  description = "Harmonize endpoint containing no protocol or path"
}

variable "ROOTCERT" {
  type = string
  description = "Harmonize SSL server certification as base64 encoded (optional)"
  default = ""
}
