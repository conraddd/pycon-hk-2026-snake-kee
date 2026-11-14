from django.urls import path

from . import views

urlpatterns = [
    path("menu", views.menu),
    path("orders", views.place_order),
    path("orders/<int:order_id>", views.order_detail),
    path("health", views.health),
]
