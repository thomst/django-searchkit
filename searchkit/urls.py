from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/<slug:app_label>/<slug:model_name>/add/", SearchkitAjaxView.as_view(), name="searchkit_new_form", kwargs=dict(add_form=True)),
    path("searchkit/<slug:app_label>/<slug:model_name>/update/", SearchkitAjaxView.as_view(), name="searchkit_update_form"),
]
