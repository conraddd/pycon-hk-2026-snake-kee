from django.urls import include, path, re_path

from shop.views import spa

urlpatterns = [
    path("api/", include("shop.urls")),
    re_path(r"^(?!api/|static/).*$", spa),  # everything else -> the React app
]
