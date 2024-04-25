# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

variable HPCR_CERT {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable SIDECAR_IMAGE {
  type        = string
  description = "sidecar image name."
}

variable REGISTRY_URL {
  type        = string
  description = "Registry URL to pull an image."
}

variable REGISTRY_USERNAME {
  type        = string
  description = "Username to access your registry."
}

variable REGISTRY_PASSWORD {
  type        = string
  description = "Password to access your registry"
}

variable REGISTRY_INSECURE {
  type        = bool
  description = "Set registry to insecure, private registry with self-signed certificate"
  default     = false
}

variable "PORT" {
  type        = string
  description = "Sidecar port."
  default     = "4000"
}

# Harmonize
variable "SK" {
  type = string
}

variable "PUB" {
  type = string
}

variable "VAULTID" {
  type = string
}

variable "HMZ_SERVER" {
  type = string
}

variable "ROOTCERT" {
  type = string
  description = "base64 encoded"
}
