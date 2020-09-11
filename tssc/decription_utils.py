"""Shared utilities for doing decryption.
"""

from tssc.utils.io import TextIOSelectiveObfuscator
from tssc.config.config_value_decryptor import ConfigValueDecryptor

class DecryptionUtils:
    """Shared utilities for doing decryption.

    Any values that are decrypted are added to the given list of TextIOSelectiveObfuscator
    of strings to obfuscate.

    Attributes
    ----------
    __obfuscation_streams : list of TextIOSelectiveObfuscator
        TextIOSelectiveObfuscators to be sure that any decrypted values are obfuscated
        on those streams.
    __config_value_decryptors : list of ConfigValueDecryptor
        ConfigValueDecryptors that can be used to decrypt given ConfigValue.
    """

    __obfuscation_streams = []
    __config_value_decryptors = []

    @staticmethod
    def register_obfuscation_stream(obfuscator_stream):
        """Add a TextIOSelectiveObfuscator to obfuscate any decrypted values on.

        Parameters
        ----------
        obfuscator_stream : TextIOSelectiveObfuscator
            TextIOSelectiveObfuscator to be sure that any decrypted values are obfuscated on.

        Raises
        ------
        AssertionError
            If given obfuscator_stream is not a type of TextIOSelectiveObfuscator
        """
        assert isinstance(obfuscator_stream, TextIOSelectiveObfuscator)
        DecryptionUtils.__obfuscation_streams.append(obfuscator_stream)

    @staticmethod
    def register_config_value_decryptor(config_value_decryptor):
        """Add a ConfigValueDecryptor that can be used to decrypt ConfigValues.

        Parameters
        ----------
        config_value_decryptor : ConfigValueDecryptor
            ConfigValueDecryptor to add to the list of decryptors that can be
            used to decrypt ConfigValues.

        Raises
        ------
        AssertionError
            If given config_value_decryptor is not a type of ConfigValueDecryptor
        """
        assert isinstance(config_value_decryptor, ConfigValueDecryptor)
        DecryptionUtils.__config_value_decryptors.append(config_value_decryptor)

    @staticmethod
    def decrypt(config_value):
        """If possible decrypt the given ConfigValue using one of the
        registered ConfigValueDecryptors.

        Parameters
        ----------
        config_value : ConfigValue
            ConfigValue to decrypt the value of with one of the
            registered ConfigValueDecryptors if possible.

        Returns
        -------
        obj or None
            Decrypted value of the given ConfigValue or
            None if none of the registered ConfigValueDecryptors can decrypt the given
            ConfigValue.
        """

        decrypted_value = None
        for config_value_decryptor in DecryptionUtils.__config_value_decryptors:
            if config_value_decryptor.can_decrypt(config_value):
                decrypted_value = config_value_decryptor.decrypt(config_value)
                break

        DecryptionUtils.__add_obfuscation_targets(decrypted_value)

        return decrypted_value

    @staticmethod
    def __add_obfuscation_targets(targets):
        if targets is not None:
            for obfuscator_stream in DecryptionUtils.__obfuscation_streams:
                obfuscator_stream.add_obfuscation_targets(targets)
