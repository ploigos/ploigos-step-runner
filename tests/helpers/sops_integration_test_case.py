import unittest
import sh
import os

from .base_test_case import BaseTestCase

class SOPSIntegrationTestCase(BaseTestCase):
    TESTS_GPG_KEY_FINGERPRINT = '6F70E1656E932EFEE8AD898A98871DAE82786C09'

    def setUp(self):
        super().setUp()

        sops_path = sh.which('sops')
        gpg_path = sh.which('gpg')
        if (sops_path is not None) and (gpg_path is not None):
            self.install_gpg_key()
        else:
            self.skipTest('sops and/or pgp not installed')

    def tearDown(self):
        super().tearDown()

        sops_path = sh.which('sops')
        gpg_path = sh.which('gpg')
        if (sops_path is not None) and (gpg_path is not None):
            self.delete_gpg_key()
        else:
            self.skipTest('sops and/or pgp not installed')

    def install_gpg_key(self):
        # install private key
        gpg_private_key_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'ploigos-step-runner-tests-private.asc'
        )
        sh.gpg( # pylint: disable=no-member
            '--import',
            gpg_private_key_path
        )

    def delete_gpg_key(self):
        try:
            # uninstall private key
            sh.gpg( # pylint: disable=no-member
                '--batch',
                '--pinentry-mode',
                'loopback',
                '--yes',
                '--delete-secret-keys',
                SOPSIntegrationTestCase.TESTS_GPG_KEY_FINGERPRINT
            )
        except:
            # don't care if this fails really
            # could fail cuz the test uninstaleld it already
            pass
