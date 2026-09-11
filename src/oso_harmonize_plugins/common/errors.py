#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#


class ConfigError(Exception):
    """Exception raised when an Environment Variable is not found"""

    pass

class SigningInProgress(Exception):
    """Exception raised while the cold bridge still has pending sign operations"""

    pass

class BroadcastError(Exception):
    """Exception raised when signed documents could not be uploaded to the
    custody API after exhausting retries"""

    pass
