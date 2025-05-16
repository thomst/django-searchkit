from django.urls import path
from .views import SearchkitAjaxView


urlpatterns = [
    path("searchkit/<slug:app_label>/<slug:model_name>/<int:index>/", SearchkitAjaxView.as_view()),
]
