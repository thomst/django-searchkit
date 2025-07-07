from django.urls import path
from .views import SearchkitView
from .views import AutocompleteView


urlpatterns = [
    path("reload/", SearchkitView.as_view(), name="searchkit-reload"),
    path("autocomplete/", AutocompleteView.as_view(), name="searchkit-autocomplete"),
]
