
import os

from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.file import (create_parent_dir,
                             download_and_decompress_source_to_destination,
                             parse_yaml_or_json_file)


class TestParseYAMLOrJASONFile(BaseTestCase):
    def test_import_yaml(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.yaml'
        )
        sample_dict = parse_yaml_or_json_file(sample_file_path)

        self.assertTrue(isinstance(sample_dict, dict))
        self.assertIsNotNone(sample_dict['step-runner-config'])
        self.assertEqual(sample_dict['step-runner-config']['global-defaults']['service-name'], 'fruit')
        self.assertEqual(sample_dict['step-runner-config']['package'][0]['implementer'], 'Maven')

    def test_import_json(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'sample.json'
        )
        sample_dict = parse_yaml_or_json_file(sample_file_path)

        self.assertTrue(isinstance(sample_dict, dict))
        self.assertIsNotNone(sample_dict['step-runner-config'])
        self.assertEqual(sample_dict['step-runner-config']['global-defaults']['service-name'], 'fruit')
        self.assertEqual(sample_dict['step-runner-config']['package'][0]['implementer'], 'Maven')

    def test_import_bad(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'bad.yaml'
        )

        with self.assertRaisesRegex(
            ValueError,
            r"Error parsing file \(.+\) as YAML or JSON:"
        ):
            parse_yaml_or_json_file(sample_file_path)

class TestDownloadAndDecompressSourceToDestination(BaseTestCase):
    def test_https_bz2(self):
        with TempDirectory() as test_dir:

            destination_path = download_and_decompress_source_to_destination(
                source_url="https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2",
                destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(destination_path, rf'{test_dir.path}/rhel-8.ds.xml$')
            with open(destination_path) as downloaded_file:
                self.assertTrue(downloaded_file.read())

    def test_https_xml(self):
        with TempDirectory() as test_dir:

            destination_path = download_and_decompress_source_to_destination(
                source_url="https://www.redhat.com/security/data/cvrf/2020/cvrf-rhba-2020-0017.xml",
                destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(destination_path, rf'{test_dir.path}/cvrf-rhba-2020-0017.xml$')
            with open(destination_path) as downloaded_file:
                self.assertTrue(downloaded_file.read())

    def test_local_file_download(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'cvrf-rhba-2020-0017.xml'
        )

        with TempDirectory() as test_dir:
            destination_path = download_and_decompress_source_to_destination(
                source_url=f"file://{sample_file_path}",
                destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(destination_path, rf'{test_dir.path}/cvrf-rhba-2020-0017.xml$')
            with open(destination_path) as downloaded_file, open(sample_file_path) as sample_file:
                downloaded_file_contents = downloaded_file.read()
                self.assertTrue(downloaded_file_contents)
                self.assertEqual(downloaded_file_contents, sample_file.read())

    def test_bad_protocol(self):
        with TempDirectory() as test_dir:

            with self.assertRaisesRegex(
                AssertionError,
                r"Unexpected error, should have been caught by step validation."
                r" Source \(.+\) must start with known protocol \(file://\|http://\|https://\)."
            ):
                download_and_decompress_source_to_destination(
                    source_url="bad://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2",
                    destination_dir=test_dir.path
                )

    def test_https_bad_url(self):
        with TempDirectory() as test_dir:
            with self.assertRaisesRegex(
                RuntimeError,
                r"Error downloading file \(.+\): HTTP Error 404: Not Found"
            ):
                download_and_decompress_source_to_destination(
                    source_url="https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/does-not-exist.ds.xml.bz2",
                    destination_dir=test_dir.path
                )

    def test_create_parent_dir(self):
        with TempDirectory() as test_dir:
            file_path = os.path.join(test_dir.path, 'hello/world/does/not/exit/foo.yml')

            self.assertFalse(os.path.exists(file_path))
            self.assertFalse(os.path.exists(os.path.dirname(file_path)))

            create_parent_dir(file_path)
            self.assertFalse(os.path.exists(file_path))
            self.assertTrue(os.path.exists(os.path.dirname(file_path)))
