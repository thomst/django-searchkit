from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/form/", SearchkitAjaxView.as_view(), name="searchkit_form"),
    path("searchkit/form/<slug:app_label>/<slug:model_name>/", SearchkitAjaxView.as_view(), name="searchkit_form_model"),
]
