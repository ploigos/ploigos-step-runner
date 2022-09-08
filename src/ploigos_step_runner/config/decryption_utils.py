"""Shared utilities for doing decryption.
"""

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.utils.io import TextIOSelectiveObfuscator
from ploigos_step_runner.utils.reflection import import_and_get_class
from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor

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

    __DEFAULT_DECRYPTORS_MODULE = 'ploigos_step_runner.config.decryptors'

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
    def create_and_register_config_value_decryptor(
        config_value_decryptor_implementer_name,
        config_value_decryptor_constructor_params=None
    ):
        """Attempts to dynamically create a ConfigValueDecryptor and register it.

        Parameters
        ----------
        config_value_decryptor_implementer_name : str
            Name of the ConfigValueDecryptor to dynamically load and create.
        config_value_decryptor_constructor_params : dict, optional
            Dictionary of constructor parameters to expand and pass to the ConfigValueDecryptor
            when it is created.

        Raises
        ------
        StepRunnerException
            If could not find class to load
            If loaded class is not a subclass of ConfigValueDecryptor

        See Also
        --------
        register_config_value_decryptor
        """
        if config_value_decryptor_constructor_params is None:
            config_value_decryptor_constructor_params = {}

        decryptor_class = DecryptionUtils.__get_decryption_class(
            config_value_decryptor_implementer_name
        )
        try:
            config_value_decryptor = decryptor_class(**config_value_decryptor_constructor_params)
            DecryptionUtils.register_config_value_decryptor(config_value_decryptor)
        except TypeError as error:
            raise ValueError(
                f"Loaded decryptor class ({decryptor_class}) failed to construct with given" +
                f" constructor arguments ({config_value_decryptor_constructor_params}): {error}"
            ) from error

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

    @staticmethod
    def __get_decryption_class(decryptor_implementer_name):
        """Given a decryptor implementer name dynamically loads the associated Class.

        Parameters
        ----------
        decryptor_implementer_name : str
            Either the short name of a ConfigValueDecryptor class which will be dynamically
            loaded from the 'ploigos_step_runner.config.decryptors' module or
            A class name that includes a dot seperated module name to load the Class from.

        Returns
        -------
        ConfigValueDecryptor
            Dynamically loaded subclass of ConfigValueDecryptor for given decryptor name.

        Raises
        ------
        StepRunnerException
            If could not find class to load
            If loaded class is not a subclass of ConfigValueDecryptor
        """
        parts = decryptor_implementer_name.split('.')
        class_name = parts.pop()
        module_name = '.'.join(parts)

        if not module_name:
            module_name = DecryptionUtils.__DEFAULT_DECRYPTORS_MODULE

        clazz = import_and_get_class(module_name, class_name)
        if not clazz:
            raise StepRunnerException(
                "Could not dynamically load decryptor implementer" +
                f" ({decryptor_implementer_name}) from module ({module_name})" +
                f" with class name ({class_name})"
            )
        if not issubclass(clazz, ConfigValueDecryptor):
            raise StepRunnerException(
                f"For decryptor implementer ({decryptor_implementer_name})" +
                f" dynamically loaded class ({clazz}) which is not sub class of" +
                f" ({ConfigValueDecryptor}) and should be."
            )

        return clazz
