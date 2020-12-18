"""ConfigValueDecryptor that uses SOPS to decyrpt ConfigValues

Also See
--------
https://github.com/mozilla/sops
"""

from io import StringIO
import json
import os.path
import re
import sys
import sh

from ploigos_step_runner.config.config_value_decryptor import ConfigValueDecryptor

class SOPS(ConfigValueDecryptor):
    """ConfigValueDecryptor that uses SOPS to decyrpt ConfigValues

    Parameters
    ----------
    additional_sops_args : list
        Additional arguments to pass to the SOPS command

    Also See
    --------
    https://github.com/mozilla/sops
    """

    SOPS_ENCRYPTED_VALUE_REGEX = r'^ENC\[.*\]$'

    def __init__(self, additional_sops_args=None):
        self.__additional_sops_args = additional_sops_args

        if not self.__additional_sops_args:
            self.__additional_sops_args = []

        super().__init__()

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
        return re.match(
            SOPS.SOPS_ENCRYPTED_VALUE_REGEX,
            str(config_value.raw_value)
        ) is not None

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

        Raises
        ------
        RuntimeError
            If error attempting to run 'sops' command
        ValueError
            If given config_value#parent_source is of type string but is not a path to a file
                that exists
            If config_value#parent_source is not of type dict or str
        """
        decrypted_value = None
        sops_path = SOPS.get_sops_value_path(config_value)

        # if source is a string assume it is a file path and decrypt from that
        # else if source is a dict then dump to json and decrypt from that
        # else error
        parent_source = config_value.parent_source
        if isinstance(parent_source, str):
            # if path exists then use as file path to decrypt from
            # else error
            if os.path.exists(parent_source):
                target_file = parent_source
                stdin = None
                input_type_arg = None
            else:
                raise ValueError(
                    f"Given config value ({config_value}) parent source ({parent_source}) " +
                    "is of type (str) but is not a path to a file that exists"
                )
        elif isinstance(parent_source, dict):
            target_file = '/dev/stdin'
            stdin = json.dumps(parent_source)
            input_type_arg = '--input-type=json'
        else:
            raise ValueError(
                f"Given config value ({config_value}) parent source ({parent_source}) " +
                f"is expected to be of type dict or str but is of type: {type(parent_source)}"
            )

        try:
            # use sops to decrypt the value
            out = StringIO()
            sh.sops( # pylint: disable=no-member
                '--decrypt',
                f'--extract={sops_path}',
                input_type_arg,
                target_file,
                _in=stdin,
                _out=out,
                _err=sys.stderr,
                *self.__additional_sops_args
            )
            decrypted_value = out.getvalue()
        except sh.ErrorReturnCode as error:
            raise RuntimeError(
                f"Error invoking sops when trying to decrypt config value ({config_value}): {error}"
            ) from error

        return decrypted_value

    @staticmethod
    def get_sops_value_path(config_value):
        """Gets a stringified version of the path parts of a ConfigValue for extration
        from a SOPS encrypted file.

        Example 1
        config_value.path_parts: ['step-runner-config', 'step-foo', 0, 'config', 'test1']
        Output: '["step-runner-config"]["step-foo"][0]["config"]["test1"]'

        Returns
        -------
        str
            SOPS path Stringified version of the path parts.
        """
        path = ""

        for path_part in config_value.path_parts:
            if isinstance(path_part, str):
                path += f"[\"{path_part}\"]"
            else:
                path += f"[{path_part}]"

        return path
