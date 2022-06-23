"""ConfigValueDecryptor that does not really decrypt anything.
It just flags ConfigValues that have potentially sensitivenames
(for example they contain "password" and "username"), so that they are obfuscated
in the PSR output ... just in case
"""
import re
from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor




class ObfuscationDefaults(ConfigValueDecryptor):
    """ConfigValueDecryptor that does not really decrypt anything.
It just flags ConfigValues that have potentially sensitivenames
(for example they contain "password" and "username"), so that they are obfuscated
in the PSR output ... just in case.

    Parameters
    ----------

    """
    def can_decrypt(self, config_value):
        for path_part in config_value.path_parts:
            if re.search(".*(password|username).*", str(path_part)):
                return True
        return False

    def decrypt(self, config_value):
        return config_value.raw_value
