from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/<slug:app_label>/<slug:model_name>/", SearchkitAjaxView.as_view(), name="searchkit_new_form"),
    path("searchkit/<slug:app_label>/<slug:model_name>/<int:index>/", SearchkitAjaxView.as_view(), name="searchkit_update_form"),
]
