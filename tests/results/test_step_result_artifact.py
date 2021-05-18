"""Test StepResultArtifact
"""

from ploigos_step_runner.results import StepResultArtifact
from tests.helpers.base_test_case import BaseTestCase


class TestStepResultArtifactTest(BaseTestCase):
    """Test StepResultArtifact
    """

    def test_name(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello'
        )

        self.assertEqual('foo', artifact.name)

    def test_value(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello'
        )

        self.assertEqual('hello', artifact.value)

    def test_description_empty(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello'
        )

        self.assertEqual("", artifact.description)

    def test_description(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        self.assertEqual("test description", artifact.description)

    def test_as_dict_no_description(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello'
        )

        expected = {'description': '', 'name': 'foo', 'value': 'hello'}
        self.assertEqual(expected, artifact.as_dict())

    def test_as_dict_with_description(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = {'description': 'test description', 'name': 'foo', 'value': 'hello'}
        self.assertEqual(expected, artifact.as_dict())

    def test___str__(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = "{'name': 'foo', 'value': 'hello', 'description': 'test description'}"
        self.assertEqual(expected, str(artifact))

    def test___repr__(self):
        artifact = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = "StepResultArtifact(name=foo, value=hello, description=test description)"
        self.assertEqual(expected, repr(artifact))

    def test___eq__(self):
        artifact1 = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        artifact2 = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        self.assertEqual(artifact1, artifact2)

    def test___nq__name(self):
        artifact1 = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        artifact2 = StepResultArtifact(
            name='bad',
            value='hello',
            description='test description'
        )

        self.assertNotEqual(artifact1, artifact2)

    def test___nq__value(self):
        artifact1 = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        artifact2 = StepResultArtifact(
            name='foo',
            value='bad',
            description='test description'
        )

        self.assertNotEqual(artifact1, artifact2)

    def test___nq__description(self):
        artifact1 = StepResultArtifact(
            name='foo',
            value='hello',
            description='test description'
        )

        artifact2 = StepResultArtifact(
            name='foo',
            value='hello',
            description='bad'
        )

        self.assertNotEqual(artifact1, artifact2)
