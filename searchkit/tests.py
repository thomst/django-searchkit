from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django import forms
from example.models import ModelA
from searchkit.forms.utils import FIELD_PLAN
from searchkit.forms.utils import SUPPORTED_FIELDS
from searchkit.forms.utils import SUPPORTED_RELATIONS
from searchkit.forms import SearchkitSearchForm
from searchkit.forms import SearchkitForm
from searchkit.forms import SearchkitFormSet


INITIAL_DATA = [
    dict(
        field='model_b__chars',
        operator='exact',
        value='anytext',
    ),
    dict(
        field='integer',
        operator='range',
        value=[1, 123],
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

add_prefix = lambda i: SearchkitFormSet(model=ModelA).add_prefix(i)
DEFAULT_PREFIX = SearchkitFormSet.get_default_prefix()
FORM_DATA = {
    'name': 'test search',                  # The name of the search.
    f'{DEFAULT_PREFIX}-TOTAL_FORMS': '6',   # Data for the managment form.
    f'{DEFAULT_PREFIX}-INITIAL_FORMS': '1', # Data for the managment form.
    f'{DEFAULT_PREFIX}-contenttype': f'{ContentType.objects.get_for_model(ModelA).pk}',
    f'{add_prefix(1)}-value_0': '1',        # Data for the range operator.
    f'{add_prefix(1)}-value_1': '123',      # Data for the range operator.
}
for i, data in enumerate(INITIAL_DATA, 0):
    prefix = SearchkitFormSet(model=ModelA).add_prefix(i)
    for key, value in data.items():
        FORM_DATA.update({f'{prefix}-{key}': value})


class CheckFormMixin:
    """
    Mixin to check the form fields and their choices.
    """
    def check_form(self, form):
        # Three fields should be generated on instantiation.
        self.assertIn('field', form.fields)
        self.assertIn('operator', form.fields)
        self.assertIn('value', form.fields)
        self.assertEqual(len(form.fields), 3)

        # Check choices of the model_field.
        form_model_field = form.fields['field']
        self.assertTrue(form_model_field.choices)
        options = [c[0] for c in form_model_field.choices]
        for model_field in ModelA._meta.fields:
            if isinstance(model_field, tuple(SUPPORTED_FIELDS)):
                self.assertIn(model_field.name, options)

        # Check choices for relational lookups.
        for model_field in ModelA._meta.fields:
            if isinstance(model_field, tuple(SUPPORTED_RELATIONS)):
                remote_fields = model_field.remote_field.model._meta.fields
                for remote_field in remote_fields:
                    if isinstance(model_field, tuple(SUPPORTED_FIELDS)):
                        lookup_path = f'{model_field.name}__{remote_field.name}'
                        self.assertIn(lookup_path, options)

        # Check the field_plan choosen based on the model_field.
        field_plan = next(iter([p for t, p in FIELD_PLAN.items() if t(form.model_field)]))
        self.assertEqual(form.field_plan, field_plan)

        # Check choices of the operator field based on the field_plan.
        operator_field = form.fields['operator']
        self.assertTrue(operator_field.choices)
        self.assertEqual(len(operator_field.choices), len(form.field_plan))
        for operator in form.field_plan.keys():
            self.assertIn(operator, [c[0] for c in operator_field.choices])


class SearchkitFormTestCase(CheckFormMixin, TestCase):

    def test_blank_searchkitform(self):
        form = SearchkitForm(ModelA, prefix=add_prefix(0))
        self.check_form(form)

        # Form should not be bound or valid.
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_model_field_data(self):
        data = {
            f'{add_prefix(0)}-field': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'field', errors)

    def test_searchkitform_with_valid_model_field_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid since no value data is provieded.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_operator_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Select a valid choice. foobar is not one of the available choices.']
        self.assertFormError(form, 'operator', errors)

    def test_searchkitform_with_valid_operator_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'exact',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid since no value data is provieded.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_valid_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'exact',
            f'{add_prefix(0)}-value': '123',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be valid.
        self.assertTrue(form.is_valid())

    def test_searchkitform_with_invalid_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'exact',
            f'{add_prefix(0)}-value': 'foobar',
        }
        form = SearchkitForm(ModelA, data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Enter a whole number.']
        self.assertFormError(form, 'value', errors)


class SearchkitFormSetTestCase(CheckFormMixin, TestCase):
    def test_blank_searchkitform(self):
        # Instantiating the formset neither with a model instance nor with model
        # related data or initial data should result in a formset without forms,
        # that is invalid and unbound.
        formset = SearchkitFormSet()
        self.assertFalse(formset.is_bound)
        self.assertFalse(formset.is_valid())

    def test_searchkit_formset_with_valid_data(self):
        formset = SearchkitFormSet(FORM_DATA)
        self.assertTrue(formset.is_valid())

    def test_searchkit_formset_with_invalid_data(self):
        data = FORM_DATA.copy()
        del data[f'{add_prefix(0)}-value']
        formset = SearchkitFormSet(data, model=ModelA)
        self.assertFalse(formset.is_valid())

        # Check error message in html.
        errors = ['This field is required.']
        self.assertFormSetError(formset, 0, 'value', errors)

    def test_searchkit_formset_with_initial_data(self):
        formset = SearchkitFormSet(initial=INITIAL_DATA, model=ModelA)
        self.assertFalse(formset.is_bound)
        self.assertFalse(formset.is_valid())
        self.assertEqual(len(formset.forms), len(INITIAL_DATA))
        for i, form in enumerate(formset.forms):
            self.assertEqual(form.initial, INITIAL_DATA[i])
            self.check_form(form)


class SearchkitSearchFormTestCase(TestCase):
    def test_searchkit_search_form_without_data(self):
        form = SearchkitSearchForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIsInstance(form.formset, SearchkitFormSet)
        self.assertEqual(form.formset.model, None)

    def test_searchkit_search_form_with_data(self):
        form = SearchkitSearchForm(FORM_DATA)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.formset, SearchkitFormSet)
        self.assertEqual(form.formset.model, ModelA)
        self.assertEqual(form.instance.data, form.formset.cleaned_data)

        # Saving the instance works.
        form.instance.save()
        self.assertTrue(form.instance.pk)

        # Using the instance data as filter rules works.
        filter_rules = form.instance.get_filter_rules()
        self.assertEqual(len(filter_rules), len(INITIAL_DATA))
        for data in INITIAL_DATA:
            self.assertIn(f"{data['field']}__{data['operator']}", filter_rules)
        queryset = form.formset.model.objects.filter(**filter_rules)
        self.assertTrue(queryset.model == ModelA)
