# Welcome to django-searchkit

[<img src="https://github.com/thomst/django-searchkit/actions/workflows/ci.yml/badge.svg">](https://github.com/thomst/django-searchkit/)
[<img src="https://coveralls.io/repos/github/thomst/django-searchkit/badge.svg?branch=main">](https://coveralls.io/github/thomst/django-searchkit?branch=main)
[<img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue">](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)
[<img src="https://img.shields.io/badge/django-4.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-orange">](https://img.shields.io/badge/django-4.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-orange)


## Description

Finally there is a real searchkit application for django that integrates best
with the django admin backend.

Build and apply complex searches on model instances right in the backend without
any coding. Save and reuse your searches by a handy django admin filter with a
single click.


## Setup

Install via pip:
```
pip install django-searchkit
```

Add `searchkit` to your `INSTALLED_APPS`:
```
INSTALLED_APPS = [
   'searchkit',
   ...
]
```

Add the `SearkitFilter` to your `ModelAdmin`:
```
from django.contrib import admin
from searchkit.filters import SearchkitFilter
from .models import MyModel


@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
   ...
    list_filter = [
      SearchkitFilter,
      ...
      ]
   ...
```

## Usage

1. Open the admin changelist of your Model.
2. Click "Add filter" on the Searchkit filter.
3. Choose the Model you want to filter.
4. Configure as many filter rules as you want.
5. Click "Save and apply"


## TODO

- Limit the choices of the model field by models that should be searchable.
- Add an apply button to the search edit page to be able to use a search without
  saving it.
- Coming from the search edit page the filtering should be done by an id__in url
  parameter, not by an search parameter as it is used by the searchkit filter.
- Preselect the right model in the model field when coming from a models
  changelist by the "Add filter" button.
- Add a public field for searches and only offer public searches in the
  searchkit filter.