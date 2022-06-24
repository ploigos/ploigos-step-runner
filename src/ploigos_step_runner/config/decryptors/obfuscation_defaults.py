"""ConfigValueDecryptor that does not really decrypt anything, but flags values that should be
obfuscated (like "password" and "username").

Parameters
----------
None
"""

import re
from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor

class ObfuscationDefaults(ConfigValueDecryptor):
    """ConfigValueDecryptor that does not really decrypt anything, but flags values that should be
    obfuscated (like "password" and "username").

    Parameters
    ----------
    None
    """

    def can_decrypt(self, config_value):
        for path_part in config_value.path_parts:
            if re.search(".*(password|username).*", str(path_part), re.IGNORECASE):
                return True
        return False

    def decrypt(self, config_value):
        return config_value.raw_value
