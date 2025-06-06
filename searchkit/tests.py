from urllib.parse import urlencode
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.urls import reverse
from example.models import ModelA
from example.management.commands.createtestdata import Command as CreateTestData
from searchkit.forms.utils import FIELD_PLAN
from searchkit.forms.utils import SUPPORTED_FIELDS
from searchkit.forms.utils import SUPPORTED_RELATIONS
from searchkit.forms import SearchkitSearchForm
from searchkit.forms import SearchkitForm
from searchkit.forms import SearchkitFormSet
from searchkit.models import Search
from searchkit import __version__


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
contenttype = ContentType.objects.get_for_model(ModelA)
DEFAULT_PREFIX = SearchkitFormSet.get_default_prefix()

def get_form_data(initial_data=INITIAL_DATA):
    count = len(initial_data)
    data = {
        'name': 'test search',                  # The name of the search.
        f'{DEFAULT_PREFIX}-TOTAL_FORMS': f'{count}',   # Data for the managment form.
        f'{DEFAULT_PREFIX}-INITIAL_FORMS': f'{count}', # Data for the managment form.
        f'{DEFAULT_PREFIX}-contenttype': f'{contenttype.pk}',  # Data for the contenttype form.
    }
    for i, d in enumerate(initial_data):
        prefix = SearchkitFormSet(model=ModelA).add_prefix(i)
        for key, value in d.items():
            if isinstance(value, list):
                for i, v in enumerate(value):
                    data.update({f'{prefix}-{key}_{i}': v})
            else:
                data.update({f'{prefix}-{key}': value})
    return data

FORM_DATA = get_form_data()


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
        self.assertIn(errors, form.errors.values())

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
        self.assertIn(errors, form.errors.values())

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
        self.assertIn(errors, form.errors.values())


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
        self.assertIn(errors, formset.forms[0].errors.values())

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


class AdminBackendTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        CreateTestData().handle()

    def setUp(self):
        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

    def test_search_form(self):
        url = reverse('admin:searchkit_search_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'searchkit-contenttype', resp.content)

    def test_add_search(self):
        url = reverse('admin:searchkit_search_add')
        data = FORM_DATA.copy()
        data['_save_and_apply'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Did we have a search?
        searches = Search.objects.all()
        self.assertEqual(len(searches), 1)

        # Change it via backend.
        url = reverse('admin:searchkit_search_change', args=(1,))
        search_name = 'Changed name'
        data['name'] = search_name
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Will the search be listed in the admin filter?
        url = reverse('admin:example_modela_changelist')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        a_html = f'<a href="?search=1">{search_name}</a>'
        self.assertInHTML(a_html, str(resp.content))


class SearchViewTest(TestCase):

    def setUp(self):
        self.initial = [
            dict(
                field='integer',
                operator='exact',
                value=1,
            )
        ]
        self.initial_range = [
            dict(
                field='integer',
                operator='range',
                value=[1,3],
            )
        ]

    def test_search_view_invalid_data(self):
        initial = self.initial.copy()
        initial[0]['value'] = 'no integer'
        data = get_form_data(initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit_form')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html_error = '<li>Enter a whole number.</li>'
        self.assertInHTML(html_error, str(resp.content))

    def test_search_view_missing_data(self):
        initial = self.initial.copy()
        del(initial[0]['value'])
        data = get_form_data(initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit_form')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html_error = '<li>This field is required.</li>'
        self.assertInHTML(html_error, str(resp.content))

    def test_search_view_with_range_operator(self):
        data = get_form_data(self.initial_range)
        url_params = urlencode(data)
        base_url = reverse('searchkit_form')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = '<input type="number" name="searchkit-modela-0-value_1" value="3" id="id_searchkit-modela-0-value_1">'
        self.assertInHTML(html, str(resp.content))

    def test_search_view_with_model(self):
        data = get_form_data(self.initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit_form_model', args=('example', 'modela'))
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_search_view_with_invalid_model(self):
        data = get_form_data(self.initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit_form_model', args=('example', 'no_model'))
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
