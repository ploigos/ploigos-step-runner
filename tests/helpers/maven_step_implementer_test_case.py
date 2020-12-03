import os
from pathlib import Path

import sh
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase


class MaveStepImplementerTestCase(BaseStepImplementerTestCase):
    @staticmethod
    def create_mvn_side_effect(
        pom_file,
        artifact_parent_dir,
        artifact_names,
        raise_error_on_tests=False
    ):
        """simulates what mvn does by touching files.

        Notes
        -----
        Supports
        - mvn clean
        - mvn install
        - mvn test
        """
        target_dir_path = os.path.join(
            os.path.dirname(os.path.abspath(pom_file)),
            artifact_parent_dir)

        def mvn_side_effect(*args, **kwargs):
            if 'clean' in args:
                if os.path.exists(target_dir_path):
                    os.rmdir(target_dir_path)

            if 'install' in args:
                os.mkdir(target_dir_path)

                for artifact_name in artifact_names:
                    artifact_path = os.path.join(
                        target_dir_path,
                        artifact_name
                    )
                    Path(artifact_path).touch()

            if 'test' in args:
                if raise_error_on_tests:
                    raise sh.ErrorReturnCode('mvn', b'mock out', b'mock error')

                os.makedirs(target_dir_path, exist_ok=True)

                for artifact_name in artifact_names:
                    artifact_path = os.path.join(
                        target_dir_path,
                        artifact_name
                    )
                    Path(artifact_path).touch()

        return mvn_side_effect
