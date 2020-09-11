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
        config_value : TSSCConfigValue
            Determine if this decryptor can decrypt this configuration value.

        Returns
        -------
        bool
            True if this ConfigValueDecryptor can decrypt the given TSSCConfigValue
            False if this ConfigValueDecryptor can NOT decrypt the given TSSCConfigValue.
        """

    @abstractmethod
    def decrypt(self, config_value):
        """Decrypt the value of the given TSSCConfigValue.

        Parameters
        ----------
        config_value : TSSCConfigValue
            Decrypt the value of this TSSCConfigValue.

        Returns
        -------
        obj or None
            Decrypted value of the TSSCConfigValue
            None if this decryptor can't decrypt the given TSSCConfigValue
        """
