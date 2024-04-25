# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

variable DEBUG {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable HPCR_CERT {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable SIDECAR_IMAGE {
  type        = string
  description = "signingservice_sidecar image name."
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

variable NOTARY_URL {
  type        = string
  description = "URL of your notary server"
  default     = ""
}

variable DCT_PUBKEY {
  type        = string
  description = "Public key for docker content trust."
  default     = ""
}

variable "PORT" {
  type        = string
  description = "Sidecar port."
  default     = "4000"
}

variable "BACKEND_ENDPOINT" {
  type        = string
}
