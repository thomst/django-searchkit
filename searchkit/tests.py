from django.test import TestCase
from django import forms
from example.models import ModelA
from .searchkit import FIELD_PLAN
from .searchkit import SearchkitForm
from .searchkit import SearchkitFormSet


INITIAL_DATA = [
    dict(
        field='chars',
        operator='exact',
        value='anytext',
    ),
    dict(
        field='integer',
        operator='range',
        value_0=1,
        value_1=123,
    ),
    dict(
        field='float',
        operator='exact',
        value='0.3',
    ),
    dict(
        field='decimal',
        operator='exact',
        value='1.23',
    ),
    dict(
        field='date',
        operator='exact',
        value='2025-05-14',
    ),
    dict(
        field='datetime',
        operator='exact',
        value='2025-05-14 08:45',
    )
]

DEFAULT_PREFIX = SearchkitFormSet.get_default_prefix()
FORM_DATA = {
    f'{DEFAULT_PREFIX}-TOTAL_FORMS': '6',
    f'{DEFAULT_PREFIX}-INITIAL_FORMS': '1'
}
for i, data in enumerate(INITIAL_DATA):
    for key, value in data.items():
        FORM_DATA.update({f'{DEFAULT_PREFIX}-{i}-{key}': value})


class SearchkitFormTestCase(TestCase):

    def check_form(self, form):
        # Three fields should be generated on instantiation.
        self.assertIn('field', form.fields)
        self.assertIn('operator', form.fields)
        self.assertIn('value', form.fields)
        self.assertEqual(len(form.fields), 3)

        # Check choices of the model_field.
        form_model_field = form.fields['field']
        self.assertTrue(form_model_field.choices)
        self.assertEqual(len(form_model_field.choices), len(ModelA._meta.fields))
        for model_field in ModelA._meta.fields:
            self.assertIn(model_field.name, [c[0] for c in form_model_field.choices])

        # Check the field_plan choosen based on the model_field.
        field_plan = next(iter([p for t, p in FIELD_PLAN.items() if t(form.model_field)]))
        self.assertEqual(form.field_plan, field_plan)

        # Check choices of the operator field based on the field_plan.
        operator_field = form.fields['operator']
        self.assertTrue(operator_field.choices)
        self.assertEqual(len(form_model_field.choices), len(form.field_plan))
        for operator in form.field_plan.keys():
            self.assertIn(operator, [c[0] for c in operator_field.choices])


    def test_blank_searchkitform(self):
        for index in range(3):
            prefix = SearchkitFormSet(ModelA).add_prefix(index)
            form = SearchkitForm(ModelA, prefix=prefix)
            self.check_form(form)

            # Form should not be bound or valid.
            self.assertFalse(form.is_bound)
            self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_model_field_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'field', errors)

    def test_searchkitform_with_valid_model_field_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_operator_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

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
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_valid_data(self):
        prefix = SearchkitFormSet(ModelA).add_prefix(0)
        data = {
            f'{prefix}-field': 'integer',
            f'{prefix}-operator': 'exact',
            f'{prefix}-value': '123',
        }
        form = SearchkitForm(ModelA, data, prefix=prefix)
        self.check_form(form)

        # Form should be valid, bound and complete
        self.assertTrue(form.is_valid())

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
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Enter a whole number.']
        self.assertFormError(form, 'value', errors)

        # get_filter_rule should raise an error.
        with self.assertRaises(forms.ValidationError):
            form.get_filter_rule()


class SearchkitFormSetTestCase(TestCase):

    def test_searchkit_formset_with_valid_data(self):
        formset = SearchkitFormSet(ModelA, FORM_DATA)
        self.assertTrue(formset.is_valid())

        # Just check if the filter rules are applicable. Result should be empty.
        self.assertFalse(ModelA.objects.filter(**formset.get_filter_rules()))

    def test_searchkit_formset_with_incomplete_data(self):
        data = FORM_DATA.copy()
        del data[f'{DEFAULT_PREFIX}-0-value']
        formset = SearchkitFormSet(ModelA, data)
        self.assertFalse(formset.is_valid())
