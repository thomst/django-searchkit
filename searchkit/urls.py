from django.urls import path
from .views import SearchkitView


urlpatterns = [
    path("reload/", SearchkitView.as_view(), name="searchkit-reload"),
]
