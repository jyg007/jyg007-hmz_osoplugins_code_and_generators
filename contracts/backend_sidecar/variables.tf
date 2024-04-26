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
