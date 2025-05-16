# Welcome to django-searchkit

[<img src="https://github.com/thomst/django-searchkit/actions/workflows/ci.yml/badge.svg">](https://github.com/thomst/django-searchkit/)
[<img src="https://coveralls.io/repos/github/thomst/django-searchkit/badge.svg?branch=main">](https://coveralls.io/github/thomst/django-searchkit?branch=main)
[<img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue">](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)
[<img src="https://img.shields.io/badge/django-3.1%20%7C%203.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1-orange">](https://img.shields.io/badge/django-3.1%20%7C%203.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1-orange)


## Description

Tired of pseudo-free money split apps with tons of advertisements? Then launch
your own little money split project with *django-searchkit* and share expenses with
friends and family using a super simple and easy to use django application based
on a well configured django admin backend.


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

## Getting started

Feel free to use the example project. (Actually it is all you need for a fully
functional money split application.)

Start it with:
```
python example/manage.py loaddata example/fixtures/testdata.json
python example/manage.py changepassword admin # Choose your password
python example/manage.py runserver
```
Then check it out by visiting `localhost:8000`.


## Usage

Each user creates expenses when needed and choose the users to share the expense with.

If you want to checkout the balance, just click the add calculation button and you will be shown a handy overview about who owes what to whom.

Save the calculation if your done dealing with the money. Open expenses will be tied to this calculation then and won't be regarded in further calculations.
