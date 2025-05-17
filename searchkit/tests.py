from django.test import TestCase
from example.models import ModelA
from .searchkit import SearchkitForm
from .searchkit import SearchkitFormSet


TEST_DATA = {
    'searchkit-TOTAL_FORMS': '6',
    'searchkit-INITIAL_FORMS': '1',
    'searchkit-0-field': 'chars',
    'searchkit-0-operator': 'exact',
    'searchkit-0-value': 'anytext',
    'searchkit-1-field': 'integer',
    'searchkit-1-operator': 'range',
    'searchkit-1-value_0': '1',
    'searchkit-1-value_1': '123',
    'searchkit-2-field': 'float',
    'searchkit-2-operator': 'exact',
    'searchkit-2-value': '0.3',
    'searchkit-3-field': 'decimal',
    'searchkit-3-operator': 'exact',
    'searchkit-3-value': '1.23',
    'searchkit-4-field': 'date',
    'searchkit-4-operator': 'exact',
    'searchkit-4-value': '2025-05-14',
    'searchkit-5-field': 'datetime',
    'searchkit-5-operator': 'exact',
    'searchkit-5-value': '2025-05-14 08:45',
}


class SearchkitFormTestCase(TestCase):

    def test_blank_searchkitform(self):
        for index in range(3):
            prefix = SearchkitFormSet(ModelA).add_prefix(index)
            form = SearchkitForm(ModelA, prefix=prefix)

            # Form should not be bound or valid.
            self.assertFalse(form.is_bound)
            self.assertFalse(form.is_valid())

            # Two fields should be present: index and model_field
            self.assertIn('field', form.fields)
            self.assertEqual(len(form.fields), 1)

            # Field name should be prefixed in hatml.
            self.assertIn(f'{form.prefix}-field', form.as_div())

            # Check choices of the model_field.
            form_model_field = form.fields['field']
            self.assertTrue(form_model_field.choices)
            self.assertEqual(len(form_model_field.choices), len(ModelA._meta.fields))
            for model_field in ModelA._meta.fields:
                self.assertIn(model_field.name, [c[0] for c in form_model_field.choices])

    def test_searchkitform_with_invalid_model_field_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Two fields should be present: index and model_field
        self.assertIn('field', form.fields)
        self.assertEqual(len(form.fields), 1)

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'field', errors)

    def test_searchkitform_with_valid_model_field_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be valid, bound and incomplete
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_complete)

        # Two fields should be present: index and model_field
        self.assertIn('field', form.fields)
        self.assertEqual(len(form.fields), 1)

        # Extend the form with operator field.
        form.extend()
        self.assertIn('operator', form.fields)
        self.assertEqual(len(form.fields), 2)

        # Check html.
        html = form.as_div()
        self.assertIn(f'{form.prefix}-operator', html)

    def test_searchkitform_with_invalid_operator_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Three fields should be present: index, model_field and operator
        self.assertEqual(len(form.fields), 2)

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'operator', errors)

    def test_searchkitform_with_valid_operator_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be valid, bound and incomplete
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_complete)

        # Two fields should be present: index and model_field
        self.assertEqual(len(form.fields), 2)

        # Extend the form with value field.
        form.extend()
        self.assertIn('value', form.fields)
        self.assertEqual(len(form.fields), 3)

        # Check html.
        html = form.as_div()
        self.assertIn(f'{form.prefix}-value', html)

    def test_searchkitform_with_valid_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
            f'{prefix}-value': '123',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be valid, bound and complete
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_complete)

        # All fields should be present.
        self.assertEqual(len(form.fields), 3)

        # Extend should do nothing now.
        form.extend()
        self.assertEqual(len(form.fields), 3)

        # Get filter rule and check if a lookup does not raises any error.
        rule = form.get_filter_rule()
        self.assertFalse(ModelA.objects.filter(**dict((rule,))))

    def test_searchkitform_with_invalid_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
            f'{prefix}-value': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # All fields should be present.
        self.assertEqual(len(form.fields), 3)

        # Check error message in html.
        errors = ['Enter a whole number.']
        self.assertFormError(form, 'value', errors)


class SearchkitFormSetTestCase(TestCase):

    def test_searchkit_formset_with_valid_data(self):
        formset = SearchkitFormSet(ModelA, TEST_DATA)
        self.assertTrue(formset.is_bound)
        self.assertTrue(formset.is_valid())
        self.assertTrue(formset.is_complete)
        # Just check if the filter rules are applicable. Result should be empty.
        self.assertFalse(ModelA.objects.filter(**formset.get_filter_rules()))

    def test_searchkit_formset_with_incomplete_data(self):
        data = TEST_DATA.copy()
        del data['searchkit-0-value']
        formset = SearchkitFormSet(ModelA, data)
        self.assertTrue(formset.is_bound)
        self.assertTrue(all(f.is_valid() for f in formset.forms))
        self.assertFalse(formset.is_valid())
        self.assertFalse(formset.is_complete)
