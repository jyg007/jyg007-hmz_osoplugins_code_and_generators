#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

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

variable "SEED" {
  type        = string
  description = "Encrypt data through the iteration pipeline (should be same value as backend plugin)"
  default     = ""
}

# Harmonize
variable "SK" {
  type = string
  description = "Private (secret) key of a registered user used to login to Harmonize"
}

variable "VAULT_ID" {
  type = string
  description = "Harmonize vault id"
}

variable "HMZ_AUTH_HOSTNAME" {
  type = string
  description = "Harmonize auth hostname containing no protocol or path"
}

variable "HMZ_API_HOSTNAME" {
  type = string
  description = "Harmonize api hostname containing no protocol or path"
}

variable "ROOTCERT" {
  type = string
  description = "Harmonize SSL server certification as base64 encoded (optional)"
  default = ""
}

variable "TOKEN_EXP" {
  type = string
  description = "Harmonize configured bearer token expiration (#h#m#s format)"
  default = "4h0m0s"
}
