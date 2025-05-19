from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/<slug:app_label>/<slug:model_name>/", SearchkitAjaxView.as_view(), name="searchkit_form"),
]
