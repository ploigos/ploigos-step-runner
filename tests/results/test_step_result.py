"""Test ResultStep
"""
from ploigos_step_runner import StepResult, WorkflowResult
from ploigos_step_runner.config import Config
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import (StepResultArtifact,
                                         StepResultEvidence, step_result)
from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.sample_step_implementers import FooStepImplementer


class TestStepResultTest(BaseTestCase):
    """Test StepResult
    """

    def test_step_name(self):
        step_result_expected = 'step1'
        step_result = StepResult('step1', 'sub1', 'implementer1')
        self.assertEqual(step_result.step_name, step_result_expected)

    def test_sub_step_name(self):
        expected = 'sub1'
        step_result = StepResult('step1', 'sub1', 'implementer1')
        self.assertEqual(step_result.sub_step_name, expected)

    def test_sub_step_implementer_name(self):
        expected = 'implementer1'
        step_result = StepResult('step1', 'sub1', 'implementer1')
        self.assertEqual(step_result.sub_step_implementer_name, expected)

    def test_success(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.success = False
        self.assertEqual(step_result.success, False)

    def test_message(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.message = 'testing'
        self.assertEqual(step_result.message, 'testing')

    def test_add_artifact(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1')
        step_result.add_artifact('artifact2', 'value2', 'description2')
        step_result.add_artifact('artifact3', 'value3')

        self.assertEqual(
            step_result.get_artifact('artifact1'),
            StepResultArtifact(
                name='artifact1',
                value='value1',
                description='description1'
            )
        )
        self.assertEqual(
            step_result.get_artifact('artifact2'),
            StepResultArtifact(
                name='artifact2',
                value='value2',
                description='description2'
            )
        )
        self.assertEqual(
            step_result.get_artifact('artifact3'),
            StepResultArtifact(
                name='artifact3',
                value='value3'
            )
        )

    def test_add_evidence(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_evidence('evidence1', 'value1', 'description1')
        step_result.add_evidence('evidence2', 'value2', 'description2')
        step_result.add_evidence('evidence3', 'value3')

        self.assertEqual(
            step_result.get_evidence('evidence1'),
            StepResultEvidence(
                name='evidence1',
                value='value1',
                description='description1'
            )
        )
        self.assertEqual(
            step_result.get_evidence('evidence2'),
            StepResultEvidence(
                name='evidence2',
                value='value2',
                description='description2'
            )
        )
        self.assertEqual(
            step_result.get_evidence('evidence3'),
            StepResultEvidence(
                name='evidence3',
                value='value3'
            )
        )

    def test_add_artifact_missing_name(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')

        with self.assertRaisesRegex(
                StepRunnerException,
                r"Name is required to add artifact"):
            step_result.add_artifact('', 'value1', 'description1')

    def test_add_evidence_missing_name(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')

        with self.assertRaisesRegex(
                StepRunnerException,
                r"Name is required to add evidence"):
            step_result.add_evidence('', 'value1', 'description1')

    def test_add_artifact_missing_value(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')

        with self.assertRaisesRegex(
                StepRunnerException,
                r"Value is required to add artifact"):
            step_result.add_artifact('name1', '', 'description1')

    def test_add_evidence_missing_value(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')

        with self.assertRaisesRegex(
                StepRunnerException,
                r"Value is required to add evidence"):
            step_result.add_evidence('name1', '', 'description1')

    def test_get_artifact(self):
        expected_artifact = StepResultArtifact(
            name='artifact1',
            value='value1',
            description='description1'
        )

        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1')
        self.assertEqual(step_result.get_artifact('artifact1'), expected_artifact)

    def test_get_evidence(self):
        expected_evidence = StepResultEvidence(
            name='evidence1',
            value='value1',
            description='description1'
        )

        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_evidence('evidence1', 'value1', 'description1')
        self.assertEqual(step_result.get_evidence('evidence1'), expected_evidence)

    def test_get_artifact_value(self):
        step_result_expected = 'value1'
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1')
        self.assertEqual(step_result.get_artifact_value('artifact1'), step_result_expected)

    def test_get_evidence_value(self):
        step_result_expected = 'value1'
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_evidence('evidence1', 'value1', 'description1')
        self.assertEqual(step_result.get_evidence_value('evidence1'), step_result_expected)

    def test_get_artifacts_property(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1')
        step_result.add_artifact('artifact2', 'value2')

        expected_artifacts = {
            'artifact1': StepResultArtifact(name='artifact1', value='value1', description='description1'),
            'artifact2': StepResultArtifact(name='artifact2', value='value2')
        }

        self.assertEqual(step_result.artifacts, expected_artifacts)

    def test_get_evidence_property(self):
        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_evidence('evidence1', 'value1', 'description1')
        step_result.add_evidence('evidence2', 'value2')

        expected_evidence = {
            'evidence1': StepResultEvidence(name='evidence1', value='value1', description='description1'),
            'evidence2': StepResultEvidence(name='evidence2', value='value2')
        }

        self.assertEqual(step_result.evidence, expected_evidence)

    def test_add_duplicate_artifact(self):
        expected_artifacts = {
            'artifact1': StepResultArtifact(name='artifact1', value='value1', description='description1'),
            'artifact2': StepResultArtifact(name='artifact2', value='lastonewins')
        }

        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_artifact('artifact1', 'value1', 'description1')
        step_result.add_artifact('artifact2', 'here')
        step_result.add_artifact('artifact2', 'andhere')
        step_result.add_artifact('artifact2', 'lastonewins')
        self.assertEqual(step_result.artifacts, expected_artifacts)

    def test_add_duplicate_evidence(self):
        expected_evidence = {
            'evidence1': StepResultEvidence(name='evidence1', value='value1', description='description1'),
            'evidence2': StepResultEvidence(name='evidence2', value='lastonewins')
        }

        step_result = StepResult('step1', 'sub1', 'implementer1')
        step_result.add_evidence('evidence1', 'value1', 'description1')
        step_result.add_evidence('evidence2', 'here')
        step_result.add_evidence('evidence2', 'andhere')
        step_result.add_evidence('evidence2', 'lastonewins')
        self.assertEqual(step_result.evidence, expected_evidence)

    def test_from_step_implementer_no_env(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        step = FooStepImplementer(
            workflow_result=WorkflowResult(),
            parent_work_dir_path=None,
            config=sub_step
        )

        step_result = StepResult.from_step_implementer(step)

        expected_step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )

        self.assertEqual(step_result, expected_step_result)

    def test_from_step_implementer_with_env(self):
        config = Config({
            'step-runner-config': {
                'foo': {
                    'implementer': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'config': {}
                }
            }
        })
        step_config = config.get_step_config('foo')
        sub_step = step_config.get_sub_step(
            'tests.helpers.sample_step_implementers.FooStepImplementer')

        step = FooStepImplementer(
            workflow_result=WorkflowResult(),
            parent_work_dir_path=None,
            config=sub_step,
            environment='blarg'
        )

        step_result = StepResult.from_step_implementer(step)

        expected_step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        self.assertEqual(step_result, expected_step_result)

    def test_artifacts_dicts_empty(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )

        self.assertEqual([], step_result.artifacts_dicts)

    def test_evidence_dicts_empty(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )

        self.assertEqual([], step_result.evidence_dicts)

    def test_artifacts_dicts_with_artifacts(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        expected_step_result_artifacts_dicts = [
            {'description': '', 'name': 'art-str', 'value': 'hello'},
            {'description': '', 'name': 'art-bool-t', 'value': True},
            {'description': '', 'name': 'art-bool-f', 'value': False},
            {'description': 'test artifact', 'name': 'art-desc', 'value': 'world'}
        ]

        self.assertEqual(expected_step_result_artifacts_dicts, step_result.artifacts_dicts)

    def test_evidence_dicts_with_evidence(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected_step_result_evidence_dicts = [
            {'description': '', 'name': 'evi-str', 'value': 'hello'},
            {'description': '', 'name': 'evi-bool-t', 'value': True},
            {'description': '', 'name': 'evi-bool-f', 'value': False},
            {'description': 'test evidence', 'name': 'evi-desc', 'value': 'world'}
        ]

        self.assertEqual(expected_step_result_evidence_dicts, step_result.evidence_dicts)

    def test_get_sub_step_result_dict(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected = {
            'artifacts': [
                {'description': '', 'name': 'art-str', 'value': 'hello'},
                {'description': '', 'name': 'art-bool-t', 'value': True},
                {'description': '', 'name': 'art-bool-f', 'value': False},
                {'description': 'test artifact', 'name': 'art-desc', 'value': 'world'}
            ],
            'evidence': [
                {'description': '', 'name': 'evi-str', 'value': 'hello'},
                {'description': '', 'name': 'evi-bool-t', 'value': True},
                {'description': '', 'name': 'evi-bool-f', 'value': False},
                {'description': 'test evidence', 'name': 'evi-desc', 'value': 'world'}
            ],
            'message': '',
            'sub-step-implementer-name': 'tests.helpers.sample_step_implementers.FooStepImplementer',
            'success': True
        }

        self.assertEqual(expected, step_result.get_sub_step_result_dict())

    def test_get_step_result_dict_no_env(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected = {
            'foo': {
                'tests.helpers.sample_step_implementers.FooStepImplementer': {
                    'artifacts': [
                        {'description': '', 'name': 'art-str', 'value': 'hello'},
                        {'description': '', 'name': 'art-bool-t', 'value': True},
                        {'description': '', 'name': 'art-bool-f', 'value': False},
                        {'description': 'test artifact', 'name': 'art-desc', 'value': 'world'}
                    ],
                    'evidence': [
                        {'description': '', 'name': 'evi-str', 'value': 'hello'},
                        {'description': '', 'name': 'evi-bool-t', 'value': True},
                        {'description': '', 'name': 'evi-bool-f', 'value': False},
                        {'description': 'test evidence', 'name': 'evi-desc', 'value': 'world'}
                    ],
                    'message': '',
                    'sub-step-implementer-name': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                    'success': True
                }
            }
        }

        self.assertEqual(expected, step_result.get_step_result_dict())

    def test_get_step_result_dict_with_env(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected = {
            'blarg': {
                'foo': {
                    'tests.helpers.sample_step_implementers.FooStepImplementer': {
                        'artifacts': [
                            {'description': '', 'name': 'art-str', 'value': 'hello'},
                            {'description': '', 'name': 'art-bool-t', 'value': True},
                            {'description': '', 'name': 'art-bool-f', 'value': False},
                            {'description': 'test artifact', 'name': 'art-desc', 'value': 'world'}
                        ],
                        'evidence': [
                            {'description': '', 'name': 'evi-str', 'value': 'hello'},
                            {'description': '', 'name': 'evi-bool-t', 'value': True},
                            {'description': '', 'name': 'evi-bool-f', 'value': False},
                            {'description': 'test evidence', 'name': 'evi-desc', 'value': 'world'}
                        ],
                        'message': '',
                        'sub-step-implementer-name': 'tests.helpers.sample_step_implementers.FooStepImplementer',
                        'success': True
                    }
                }
            }
        }

        self.assertEqual(expected, step_result.get_step_result_dict())

    def test___str__(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected = "{'step-name': 'foo', 'sub-step-name': "\
        "'tests.helpers.sample_step_implementers.FooStepImplementer', "\
        "'sub-step-implementer-name': 'tests.helpers.sample_step_implementers.FooStepImplementer', "\
        "'environment': 'blarg', 'success': True, 'message': '', "\
        "'artifacts': [{'name': 'art-str', 'value': 'hello', 'description': ''}, "\
        "{'name': 'art-bool-t', 'value': True, 'description': ''}, "\
        "{'name': 'art-bool-f', 'value': False, 'description': ''}, "\
        "{'name': 'art-desc', 'value': 'world', 'description': 'test artifact'}], "\
        "'evidence': [{'name': 'evi-str', 'value': 'hello', 'description': ''}, "\
        "{'name': 'evi-bool-t', 'value': True, 'description': ''}, "\
        "{'name': 'evi-bool-f', 'value': False, 'description': ''}, "\
        "{'name': 'evi-desc', 'value': 'world', 'description': 'test evidence'}]}"

        self.assertEqual(expected, str(step_result))

    def test___repr__(self):
        step_result = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        expected = "StepResult(step_name=foo,sub_step_name=tests.helpers." \
            "sample_step_implementers.FooStepImplementer,sub_step_implementer_name=" \
            "tests.helpers.sample_step_implementers.FooStepImplementer,environment=" \
            "blarg,success=True,message=,artifacts=[{'name': 'art-str', 'value': 'hello', "\
            "'description': ''}, {'name': 'art-bool-t', 'value': True, 'description': ''}, "\
            "{'name': 'art-bool-f', 'value': False, 'description': ''}, "\
            "{'name': 'art-desc', 'value': 'world', 'description': 'test artifact'}]"\
            "evidence=[{'name': 'evi-str', 'value': 'hello', 'description': ''}, "\
            "{'name': 'evi-bool-t', 'value': True, 'description': ''}, "\
            "{'name': 'evi-bool-f', 'value': False, 'description': ''}, "\
            "{'name': 'evi-desc', 'value': 'world', 'description': 'test evidence'}])"


        print(str(repr(step_result)))

        self.assertEqual(expected, repr(step_result))

    def test___eq__(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result1.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result1.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result1.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result1.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result1.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result1.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result1.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result1.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        step_result2 = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result2.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result2.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result2.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result2.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result2.add_evidence(
            name='evi-str',
            value='hello'
        )
        step_result2.add_evidence(
            name='evi-bool-t',
            value=True
        )
        step_result2.add_evidence(
            name='evi-bool-f',
            value=False
        )
        step_result2.add_evidence(
            name='evi-desc',
            value='world',
            description='test evidence'
        )

        self.assertEqual(step_result1, step_result2)

    def test___nq___artifacts(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )
        step_result1.add_artifact(
            name='art-str',
            value='hello'
        )
        step_result1.add_artifact(
            name='art-bool-t',
            value=True
        )
        step_result1.add_artifact(
            name='art-bool-f',
            value=False
        )
        step_result1.add_artifact(
            name='art-desc',
            value='world',
            description='test artifact'
        )

        step_result2 = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        self.assertNotEqual(step_result1, step_result2)

    def test___nq___step_name(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        step_result2 = StepResult(
            step_name='foo1',
            sub_step_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        self.assertNotEqual(step_result1, step_result2)

    def test___nq___sub_step_name(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='a',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        step_result2 = StepResult(
            step_name='foo',
            sub_step_name='b',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        self.assertNotEqual(step_result1, step_result2)

    def test___nq___sub_step_implementer_name(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='a',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='blarg'
        )

        step_result2 = StepResult(
            step_name='foo',
            sub_step_name='a',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.BarStepImplementer',
            environment='blarg'
        )

        self.assertNotEqual(step_result1, step_result2)

    def test___nq___environment(self):
        step_result1 = StepResult(
            step_name='foo',
            sub_step_name='a',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='a'
        )

        step_result2 = StepResult(
            step_name='foo',
            sub_step_name='a',
            sub_step_implementer_name='tests.helpers.sample_step_implementers.FooStepImplementer',
            environment='b'
        )

        self.assertNotEqual(step_result1, step_result2)
