from django.urls import path
from .views import SearchkitAjaxView
from .views import SearchkitFilterView


urlpatterns = [
    path("searchkit/form/<slug:app_label>/<slug:model_name>/", SearchkitAjaxView.as_view(), name="searchkit_form"),
    path("searchkit/filter/<slug:app_label>/<slug:model_name>/", SearchkitFilterView.as_view(), name="searchkit_filter"),
]
