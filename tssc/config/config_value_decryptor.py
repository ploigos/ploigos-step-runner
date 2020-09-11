"""Abstract class for config value decryptor implementers.
"""

from abc import ABC, abstractmethod

class ConfigValueDecryptor(ABC):
    """Abstract class for config value decryptor implementers.
    """

    @abstractmethod
    def can_decrypt(self, config_value):
        """Determine if a given config value can be decrypted by this decryptor.

        Parameters
        ----------
        config_value : ConfigValue
            Determine if this decryptor can decrypt this configuration value.

        Returns
        -------
        bool
            True if this ConfigValueDecryptor can decrypt the given ConfigValue
            False if this ConfigValueDecryptor can NOT decrypt the given ConfigValue.
        """

    @abstractmethod
    def decrypt(self, config_value):
        """Decrypt the value of the given ConfigValue.

        Parameters
        ----------
        config_value : ConfigValue
            Decrypt the value of this ConfigValue.

        Returns
        -------
        obj or None
            Decrypted value of the ConfigValue
            None if this decryptor can't decrypt the given ConfigValue
        """
