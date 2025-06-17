from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/", SearchkitAjaxView.as_view(), name="searchkit_form"),
]
