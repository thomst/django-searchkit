# Welcome to django-searchkit

[<img src="https://github.com/thomst/django-searchkit/actions/workflows/ci.yml/badge.svg">](https://github.com/thomst/django-searchkit/)
[<img src="https://coveralls.io/repos/github/thomst/django-searchkit/badge.svg?branch=main">](https://coveralls.io/github/thomst/django-searchkit?branch=main)
[<img src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue">](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)
[<img src="https://img.shields.io/badge/django-4.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-orange">](https://img.shields.io/badge/django-4.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2-orange)


## Description

Finally there is a real searchkit application for django that integrates best
with the django admin backend.

You have tons of admin changelist filters and still you are not able to filter your items exactly as you need it?
Or once and again you need a combination of several changelist filters and you are tired of waiting for each filter being applied one after the other?
Or you just don't want to write a custom changlist filter for each special requirement of your customers.

Then django-searchkit is what you want. Give it a try.


## Features
- Build and apply complex searches using a dynamic form.
- Add as many filter rules as you want using django's various [field lookups](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#field-lookups).
- Save and reuse your searches at any time by a handy admin changelist filter.


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
2. Click the "Add filter" button of the Searchkit filter.
3. Give your Filter a name.
4. Configure as many filter rules as you want.
5. Click "Save and apply".
6. Reuse your filter whenever you want using the Searchkit filter section.
