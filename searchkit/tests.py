from django.test import TestCase
from example.models import ModelA
from .searchkit import SearchkitFormset
from .searchkit import SearchkitForm


TEST_DATA = {
    'index': [0, 1, 2, 3, 4, 5],
    '0_model_field': 'chars',
    '0_operator': 'exact',
    '0_value0': 'anytext',
    '1_model_field': 'integer',
    '1_operator': 'exact',
    '1_value0': '123',
    '2_model_field': 'float',
    '2_operator': 'exact',
    '2_value0': '0.3',
    '3_model_field': 'decimal',
    '3_operator': 'exact',
    '3_value0': '1,23',
    '4_model_field': 'date',
    '4_operator': 'exact',
    '4_value0': '2025-05-14',
    '5_model_field': 'datetime',
    '5_operator': 'exact',
    '5_value0': '2025-05-14 08:45',
}


class SearchkitFormTestCase(TestCase):

    def test_blank_searchkitform(self):
        for index in range(3):
            form = SearchkitForm(ModelA, index)

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
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'foobar',
        }
        form = SearchkitForm(ModelA, index, data)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Two fields should be present: index and model_field
        self.assertIn('field', form.fields)
        self.assertEqual(len(form.fields), 1)

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'field', errors)

    def test_searchkitform_with_valid_model_field_data(self):
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'integer',
        }
        form = SearchkitForm(ModelA, index, data)

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
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'foobar',
        }
        form = SearchkitForm(ModelA, index, data)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Three fields should be present: index, model_field and operator
        self.assertEqual(len(form.fields), 2)

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'operator', errors)

    def test_searchkitform_with_valid_operator_data(self):
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
        }
        form = SearchkitForm(ModelA, index, data)

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
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
            f'{prefix}-value': '123',
        }
        form = SearchkitForm(ModelA, index, data)

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
        index = 0
        prefix = SearchkitForm(ModelA, index).prefix
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
            f'{prefix}-value': 'foobar',
        }
        form = SearchkitForm(ModelA, index, data)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # All fields should be present.
        self.assertEqual(len(form.fields), 3)

        # Check error message in html.
        errors = ['Enter a whole number.']
        self.assertFormError(form, 'value', errors)



# class SearchkitFormSetTestCase(TestCase):

#     def test_searchkit_formset_with_valid_data(self):
#         formset = SearchkitFormset(TEST_DATA)
#         self.assertEqual(len(formset.forms), 6)
#         html = str(formset)
#         self.assertInHTML('index', html, 6)
#         for key, value in TEST_DATA.items():
#             self.assertInHTML(key, html)
#             self.assertInHTML(value, html)
