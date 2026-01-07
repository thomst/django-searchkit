import os, sys, json
from pprint import pprint
from decimal import Decimal
from contextlib import contextmanager
from urllib.parse import urlencode
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.urls import reverse
from example.models import ModelA, ModelB
from example.management.commands.createtestdata import Command as CreateTestData
from searchkit.forms import FieldPlan
from searchkit.utils import ModelTree
from searchkit.forms import SearchForm
from searchkit.forms import SearchkitModelForm
from searchkit.forms import BaseSearchkitFormSet
from searchkit.forms import searchkit_formset_factory
from searchkit.models import Search
from searchkit.views import AutocompleteView
from searchkit import __version__
from django.db.models import Q


# Check django version.
import django
print(f'DJANGO-VERSION: {django.VERSION}')


SearchkitFormSet = searchkit_formset_factory(model=ModelA)
SearchkitForm = SearchkitFormSet.form


INITIAL_DATA = [
    dict(
        field='id',
        operator='gt',
        value=123,
    ),
    dict(
        field='id',
        operator='range',
        value=[123, 432],
    ),
    dict(
        negation=True,
        logical_operator='or',
        field='boolean',
        operator='exact',
        value=True,
    ),
    dict(
        negation=True,
        logical_operator='or',
        field='chars',
        operator='in',
        value=['ModelA chars 1', 'ModelA chars 2'],
    ),
    dict(
        field='chars_choices',
        operator='iexact',
        value='one',
    ),
    dict(
        field='text',
        operator='icontains',
        value='xyz',
    ),
    dict(
        field='email',
        operator='istartswith',
        value='user12',
    ),
    dict(
        field='url',
        operator='iregex',
        value='^.+\.com/[a-z]+/66$',
    ),
    dict(
        field='uuid',
        operator='iendswith',
        value='x',
    ),
    dict(
        field='integer',
        operator='range',
        value=[1, 123],
    ),
    dict(
        field='big_integer',
        operator='gt',
        value=1000,
    ),
    dict(
        field='integer_choices',
        operator='exact',
        value=3,
    ),
    dict(
        field='float',
        operator='lte',
        value=10.02,
    ),
    dict(
        field='decimal',
        operator='gte',
        value=Decimal('2.2'),
    ),
    dict(
        field='date',
        operator='gt',
        value='2020-05-14',
    ),
    dict(
        field='time',
        operator='lte',
        value='22:45',
    ),
    dict(
        field='datetime',
        operator='exact',
        value=['2025-05-14', '08:45'],
    ),
    dict(
        field='model_b__chars',
        operator='isnull',
        value=False,
    ),
    dict(
        field='model_b__model_c__boolean',
        operator='exact',
        value=True,
    ),
]


add_prefix = lambda i: SearchkitFormSet().add_prefix(i)
DEFAULT_PREFIX = SearchkitFormSet.get_default_prefix()


def get_form_data(initial_data=INITIAL_DATA, max=None):
    modela_ct = ContentType.objects.get_for_model(ModelA)
    count = max or len(initial_data)
    data = {
        'name': 'test search',                          # The name of the search.
        'searchkit_model': f'{modela_ct.pk}',         # Data for the searchkit-model form.
        f'{DEFAULT_PREFIX}-TOTAL_FORMS': f'{count}',    # Data for the managment form.
        f'{DEFAULT_PREFIX}-INITIAL_FORMS': f'{count}',  # Data for the managment form.
    }
    for i, item_data in enumerate(initial_data):
        prefix = SearchkitFormSet().add_prefix(i)
        for key, value in item_data.items():
            # Create multiple value fields for range operators or the datetime
            # field. Exclude the in operator since it expects a list as value.
            if isinstance(value, list) and item_data['operator'] != 'in':
                data.update({f'{prefix}-{key}_{0}': value[0]})
                data.update({f'{prefix}-{key}_{1}': value[1]})
            else:
                data.update({f'{prefix}-{key}': value})

        # Break if max is set and reached.
        if max and i + 1 >= max:
            break

    return data


@contextmanager
def silence_stdout():
    old_stdout = sys.stdout
    try:
        with open(os.devnull, "w") as dev_null:
            sys.stdout = dev_null
            yield dev_null
    finally:
        sys.stdout = old_stdout



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

        # Check logic form.
        self.assertTrue(form.logic_form)
        self.assertIn('negation', form.logic_form.fields)
        if int(form.prefix.split('-')[-1]) == 0:
            # The first form should not have a logical operator.
            self.assertNotIn('logical_operator', form.logic_form.fields)
            self.assertEqual(len(form.logic_form.fields), 1)
        else:
            self.assertIn('logical_operator', form.logic_form.fields)
            self.assertEqual(len(form.logic_form.fields), 2)

        # Check field choices for the model.
        form_model_field = form.fields['field']
        self.assertTrue(form_model_field.choices)
        options = [c[0] for g in form_model_field.choices for c in g[1]]
        tree = ModelTree(ModelA)
        for node in tree.iterate():
            for model_field in node.model._meta.fields:
                if not any(isinstance(model_field, f) for f in FieldPlan.SUPPORTED_FIELD_TYPES):
                    continue
                if node.is_root:
                    self.assertIn(model_field.name, options)
                else:
                    self.assertIn(f'{node.field_path}__{model_field.name}', options)

        # Check operator field has choices.
        self.assertTrue(form.fields['operator'].choices)


class CreateTestDataMixin:
    @classmethod
    def setUpTestData(cls):
        with silence_stdout():
            CreateTestData().handle()


class SearchkitFormTestCase(CheckFormMixin, TestCase):

    def test_blank_searchkitform(self):
        form = SearchkitForm(prefix=add_prefix(0))
        self.check_form(form)

        # Form should not be bound or valid.
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_model_field_data(self):
        data = {
            f'{add_prefix(0)}-field': 'foobar',
        }
        form = SearchkitForm(data, prefix=add_prefix(0))
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
        form = SearchkitForm(data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid since no value data is provieded.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_invalid_operator_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'foobar',
        }
        form = SearchkitForm(data, prefix=add_prefix(0))
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
        form = SearchkitForm(data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid since no value data is provieded.
        self.assertFalse(form.is_valid())

    def test_searchkitform_with_valid_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'exact',
            f'{add_prefix(0)}-value': '123',
        }
        form = SearchkitForm(data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be valid.
        self.assertTrue(form.is_valid())

    def test_searchkitform_with_invalid_data(self):
        data = {
            f'{add_prefix(0)}-field': 'integer',
            f'{add_prefix(0)}-operator': 'exact',
            f'{add_prefix(0)}-value': 'foobar',
        }
        form = SearchkitForm(data, prefix=add_prefix(0))
        self.check_form(form)

        # Form should be invalid.
        self.assertFalse(form.is_valid())

        # Check error message in html.
        errors = ['Enter a whole number.']
        self.assertIn(errors, form.errors.values())


class SearchkitFormSetTestCase(CreateTestDataMixin, CheckFormMixin, TestCase):
    def setUp(self):
        self.data = get_form_data()

    def test_blank_searchkitform(self):
        # Instantiating the formset neither with a model instance nor with model
        # related data or initial data should result in a formset without forms,
        # that is invalid and unbound.
        formset = SearchkitFormSet()
        self.assertFalse(formset.is_bound)
        self.assertFalse(formset.is_valid())

    def test_searchkit_formset_with_valid_data(self):
        formset = SearchkitFormSet(self.data)
        self.assertTrue(formset.is_valid())

    def test_searchkit_formset_with_invalid_data(self):
        data = self.data.copy()
        del data[f'{add_prefix(0)}-value']
        formset = SearchkitFormSet(data)
        self.assertFalse(formset.is_valid())

        # Check error message in html.
        errors = ['This field is required.']
        self.assertIn(errors, formset.forms[0].errors.values())

    def test_searchkit_formset_with_initial_data(self):
        formset_class = searchkit_formset_factory(model=ModelA, extra=0)
        formset = formset_class(initial=INITIAL_DATA)
        self.assertFalse(formset.is_bound)
        self.assertFalse(formset.is_valid())
        self.assertEqual(len(formset.forms), len(INITIAL_DATA))
        for i, form in enumerate(formset.forms):
            self.assertEqual(form.initial, INITIAL_DATA[i])
            self.check_form(form)


class SearchkitSearchFormTestCase(CreateTestDataMixin, TestCase):
    def setUp(self):
        self.data = get_form_data()

    def test_searchkit_search_form_without_data(self):
        form = SearchForm()
        self.assertFalse(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertIsInstance(form.formset, BaseSearchkitFormSet)
        self.assertEqual(form.formset.model, None)

    def test_searchkit_search_form_with_data(self):
        form = SearchForm(self.data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.formset, BaseSearchkitFormSet)
        self.assertEqual(form.formset.model, ModelA)
        self.assertEqual(form.instance.data, form.formset.cleaned_data)

        # Saving the instance works.
        form.instance.save()
        self.assertTrue(form.instance.pk)

        # Check the Q object of a search instance.
        q = form.instance.as_q()
        self.assertIsInstance(q, Q)
        self.assertTrue(len(q) > 0)

        # Get field lookups from the q object and check them against the initial
        # data.
        def get_field_lookups(q):
            lookups = []
            for child in q.children:
                if hasattr(child, 'children'):  # It's a nested Q object
                    lookups.extend(get_field_lookups(child))
                elif isinstance(child, tuple):  # It's a field lookup
                    lookups.append(child[0])
            return lookups
        lookups = get_field_lookups(q)
        for data in INITIAL_DATA:
            self.assertIn(f'{data["field"]}__{data["operator"]}', lookups)


class SearchkitModelFormTestCase(TestCase):
    def test_searchkit_model_form_choices(self):
        form = SearchkitModelForm()
        labels = [c[1] for c in form.fields['searchkit_model'].choices]
        self.assertEqual(len(labels), 4)
        self.assertEqual('select a model', labels[0].lower())
        self.assertEqual('example | model a', labels[1].lower())
        self.assertEqual('example | model b', labels[2].lower())
        self.assertEqual('example | model c', labels[3].lower())


class AdminBackendTest(CreateTestDataMixin, TestCase):

    def setUp(self):
        admin = User.objects.get(username='admin')
        self.client.force_login(admin)
        self.modela_ct = ContentType.objects.get_for_model(ModelA)
        self.data = get_form_data()


    def test_search_form(self):
        url = reverse('admin:searchkit_search_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        select = '<select name="searchkit_model" class="searchkit-reload" data-reload-handler="change" data-total-forms="1" required id="id_searchkit_model">'
        for snippet in select.split(' '):
            self.assertIn(snippet, str(resp.content))

    def test_search_form_with_initial(self):
        url = reverse('admin:searchkit_search_add') + f'?searchkit_model={self.modela_ct.id}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        select = '<select name="searchkit_model" class="searchkit-reload" data-reload-handler="change" data-total-forms="1" required id="id_searchkit_model">'
        for snippet in select.split(' '):
            self.assertIn(snippet, str(resp.content))
        self.assertIn(f'<option value="{self.modela_ct.id}" selected>', str(resp.content))
        self.assertIn('name="searchkit-example-modela-0-field"', str(resp.content))

    def test_add_search(self):
        # Create a search object via the admin backend.
        url = reverse('admin:searchkit_search_add')
        data = self.data.copy()
        data['_save_and_apply'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(Search.objects.all()), 1)

        # Load the saved search.
        url = reverse('admin:searchkit_search_change', args=(1,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<select name="searchkit_model"', str(resp.content))
        self.assertIn(f'<option value="{self.modela_ct.id}" selected>', str(resp.content))
        self.assertIn('name="searchkit-example-modela-0-field"', str(resp.content))
        self.assertIn('value="ModelA chars 1"', str(resp.content))

        # Change it via admin backend.
        data['name'] = 'Changed name'
        data['searchkit-example-modela-0-field'] = 'boolean'
        data['searchkit-example-modela-0-operator'] = 'exact'
        data['searchkit-example-modela-0-value'] = 'true'
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Search.objects.get(pk=1).name, data['name'])

        # Will the search be listed in the admin filter?
        url = reverse('admin:example_modela_changelist')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('href="?search=1"', str(resp.content))
        self.assertIn(data['name'], str(resp.content))

    def test_change_search(self):
        # Create a search object via the admin backend.
        url = reverse('admin:searchkit_search_add')
        data = get_form_data(INITIAL_DATA, max=1)
        data['_save_and_apply'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(Search.objects.all()), 1)

        # Change it via admin backend using a different model.
        url = reverse('admin:searchkit_search_change', args=(1,))
        data = get_form_data([], max=1)
        data['name'] = 'Using ModelB'
        data['searchkit_model'] = ContentType.objects.get_for_model(ModelB).pk
        data['searchkit-example-modelb-0-field'] = 'chars'
        data['searchkit-example-modelb-0-operator'] = 'icontains'
        data['searchkit-example-modelb-0-value'] = 'abc'
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('was changed successfully', str(resp.content))
        self.assertEqual(Search.objects.get(pk=1).name, data['name'])

    def test_apply_search(self):
        # Create a search object via the admin backend.
        url = reverse('admin:searchkit_search_add')
        data = self.data.copy()
        data['_apply'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Invalid base64 encoded json data.", str(resp.content))
        self.assertNotIn("No valid search data provided.", str(resp.content))
        self.assertEqual(len(Search.objects.all()), 0)

    def test_apply_saved_search(self):
        # Create a search object via the admin backend.
        url = reverse('admin:searchkit_search_add')
        data = self.data.copy()
        data['_save'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(Search.objects.all()), 1)

        # Apply the saved search.
        url = reverse('admin:searchkit_search_change', args=(1,))
        data = self.data.copy()
        data['_apply'] = True
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(Search.objects.all()), 1)
        redirect_url = resp.redirect_chain[0][0]
        base46_string = redirect_url.split('=')[1]
        self.assertTrue(base46_string)


class SearchkitViewTest(CreateTestDataMixin, TestCase):

    def setUp(self):
        admin = User.objects.get(username='admin')
        self.client.force_login(admin)

        self.initial = [
            dict(
                field='integer',
                operator='iexact',
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

    def test_searchkit_view_with_anonymous_user(self):
        self.client.logout()
        data = get_form_data(self.initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_searchkit_view_invalid_data(self):
        initial = self.initial.copy()
        initial[0]['value'] = 'no integer'
        data = get_form_data(initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # There shouldn't be any errors since they are removed by the view.
        self.assertNotIn('.errorlist', str(resp.content))

    def test_searchkit_view_with_missing_data(self):
        initial = self.initial.copy()
        del(initial[0]['value'])
        data = get_form_data(initial)
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # There shouldn't be any errors since they are removed by the view.
        self.assertNotIn('.errorlist', str(resp.content))

    def test_searchkit_view_with_range_operator(self):
        data = get_form_data(self.initial_range)
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = '<input type="number" name="searchkit-example-modela-0-value_1" value="3" id="id_searchkit-example-modela-0-value_1">'
        self.assertInHTML(html, resp.content.decode('utf-8'))

    def test_searchkit_view_with_model(self):
        data = get_form_data(self.initial)
        data['searchkit_model'] = ContentType.objects.get_for_model(ModelA).pk
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_searchkit_view_with_invalid_model(self):
        data = get_form_data(self.initial)
        data['searchkit_model'] = 9999  # Non-existing content type.
        url_params = urlencode(data)
        base_url = reverse('searchkit-reload')
        url = f'{base_url}?{url_params}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)


class Select2ViewTestCase(CreateTestDataMixin, TestCase):
    def setUp(self):
        admin = User.objects.get(username='admin')
        self.client.force_login(admin)
        self.url = reverse('searchkit-autocomplete')
        self.data = {
            'sk_autocomplete_app_label': ModelA._meta.app_label,
            'sk_autocomplete_model_name': ModelA._meta.model_name,
            'sk_autocomplete_field_name': 'chars',
        }

    def test_select2_view_with_anonymous_user(self):
        self.client.logout()
        data = self.data.copy()
        url = f'{self.url}?{urlencode(self.data)}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_select2_view_without_data(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_select2_view_with_base_data(self):
        url = f'{self.url}?{urlencode(self.data)}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertTrue('pagination' in result)
        self.assertTrue(result['pagination']['more'])
        self.assertTrue('results' in result)
        self.assertEqual(len(result['results']), AutocompleteView.paginate_by)

    def test_select2_view_with_paging(self):
        data = self.data.copy()
        data['page'] = 10
        url = f'{self.url}?{urlencode(data)}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertTrue('pagination' in result)
        self.assertTrue(result['pagination']['more'])
        self.assertTrue('results' in result)
        self.assertEqual(len(result['results']), AutocompleteView.paginate_by)

    def test_select2_view_with_search_term(self):
        data = self.data.copy()
        data['term'] = 'Model'
        url = f'{self.url}?{urlencode(data)}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertTrue('pagination' in result)
        self.assertFalse(result['pagination']['more'])
        self.assertTrue('results' in result)
        field_name = self.data['sk_autocomplete_field_name']
        lookup = f'{field_name}__icontains'
        queryset = ModelA.objects.order_by(lookup)
        queryset = queryset.values_list(field_name)
        queryset = queryset.filter(**{lookup:data['term']})
        queryset = queryset.distinct()
        self.assertEqual(len(result['results']), queryset.count())


class SearchTestCase(CreateTestDataMixin, TestCase):
    def test_search_as_q(self):
        search = Search.objects.create(
            name='Test search',
            contenttype=ContentType.objects.get_for_model(ModelA),
            data=INITIAL_DATA
        )
        q = search.as_q()
        self.assertIsInstance(q, Q)
        self.assertTrue(len(q) > 0)

    def test_search_details(self):
        search = Search.objects.create(
            name='Test search',
            description='My description',
            contenttype=ContentType.objects.get_for_model(ModelA),
            data=INITIAL_DATA
        )
        details = search.details
        self.assertEqual(len(INITIAL_DATA), len(details.splitlines()))
