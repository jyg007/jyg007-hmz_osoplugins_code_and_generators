#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

variable "PREFIX" {
  type        = string
}

variable "IMAGE" {
  type        = string
  description = "GREP11 image name with registry"
}

variable "PORT" {
  type        = string
  description = "GREP11 port number"
  default     = "9876"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "DOMAIN" {
  type        =  string
  description = "Crypto appliance domain"
}

variable "C16_CLIENT_HOST" {
  type        = string
  default     = "192.168.128.4"
  description = "Crypto appliance host endpoint"
}

variable "C16_CLIENT_PORT" {
  type       = string
  default    = "9001"
}

variable "C16_CLIENT_LOGLEVEL" {
  type        = string
  default     = "debug"
  validation {
    condition     = contains(["trace", "debug", "info", "warn", "err", "error", "critical", "off"], var.C16_CLIENT_LOGLEVEL)
    error_message = "Valid values for var: C16_CLIENT_LOGLEVEL are (trace, debug, info, warn, err, error, critical, off)."
  }
}

variable "C16_CLIENT_KEY" {
  type        = string
  description = "Crypto appliance client key"
}

variable "C16_CLIENT_CERT" {
  type        = string
  description = "Crypto appliance client certificate"
}

variable "C16_CA_CERT" {
  type        = string
  description = "Crypto appliance CA certificate"
}

variable "CERT_VALIDITY_PERIOD" {
  type = string
  default = "720"
}

variable "STATIC_IP" {
  type        = bool
  description = "Deploying via OSO release that supports static IP"
  default     = true
}

variable "STATIC_IP_ADDRS" {
  type        = list(string)
  description = "Static IP addresses assigned to grep11 VM"
  default     = ["192.168.64.21", "192.168.96.21", "192.168.128.21"]
}
