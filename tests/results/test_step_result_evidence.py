"""Test StepResultEvidence
"""

from ploigos_step_runner.results import StepResultEvidence
from tests.helpers.base_test_case import BaseTestCase


class TestStepResultEvidenceTest(BaseTestCase):
    """Test StepResultEvidence
    """

    def test_name(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello'
        )

        self.assertEqual('foo', evidence.name)

    def test_value(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello'
        )

        self.assertEqual('hello', evidence.value)

    def test_description_empty(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello'
        )

        self.assertEqual("", evidence.description)

    def test_description(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        self.assertEqual("test description", evidence.description)

    def test_as_dict_no_description(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello'
        )

        expected = {'description': '', 'name': 'foo', 'value': 'hello'}
        self.assertEqual(expected, evidence.as_dict())

    def test_as_dict_with_description(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = {'description': 'test description', 'name': 'foo', 'value': 'hello'}
        self.assertEqual(expected, evidence.as_dict())

    def test___str__(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = "{'name': 'foo', 'value': 'hello', 'description': 'test description'}"
        self.assertEqual(expected, str(evidence))

    def test___repr__(self):
        evidence = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        expected = "StepResultEvidence(name=foo, value=hello, description=test description)"
        self.assertEqual(expected, repr(evidence))

    def test___eq__(self):
        evidence1 = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        evidence2 = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        self.assertEqual(evidence1, evidence2)

    def test___nq__name(self):
        evidence1 = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        evidence2 = StepResultEvidence(
            name='bad',
            value='hello',
            description='test description'
        )

        self.assertNotEqual(evidence1, evidence2)

    def test___nq__value(self):
        evidence1 = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        evidence2 = StepResultEvidence(
            name='foo',
            value='bad',
            description='test description'
        )

        self.assertNotEqual(evidence1, evidence2)

    def test___nq__description(self):
        evidence1 = StepResultEvidence(
            name='foo',
            value='hello',
            description='test description'
        )

        evidence2 = StepResultEvidence(
            name='foo',
            value='hello',
            description='bad'
        )

        self.assertNotEqual(evidence1, evidence2)
