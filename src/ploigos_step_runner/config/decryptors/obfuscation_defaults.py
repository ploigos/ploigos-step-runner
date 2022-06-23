
from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor

import re

# ConfigValueDecryptor that does not really decrypt anything. It just flags ConfigValues that have potentially sensitive
# names (for example they contain "password" and "username"), so that they are obfuscated
# in the PSR output ... just in case.
class ObfuscationDefaults(ConfigValueDecryptor):

    def __init__(self, additional_sops_args=None):
        super().__init__()

    def can_decrypt(self, config_value):
        for path_part in config_value.path_parts:
            if re.search(".*(password|username).*", path_part.__str__()):
                return True
        return False

    def decrypt(self, config_value):
        return config_value.raw_value
