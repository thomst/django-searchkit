from django.urls import path
from .views import SearchkitView


urlpatterns = [
    path("searchkit/", SearchkitView.as_view(), name="searchkit_form"),
]
