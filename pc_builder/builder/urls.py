from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("konfigurator/", views.builder_view, name="builder"),
    path("rejestracja/", views.register_view, name="register"),
    path("api/zestaw/", views.api_build_summary, name="api_build"),
    path("api/kategoria/<slug:slug>/", views.api_category_components, name="api_category"),
    path("api/ustaw/", views.api_set_part, name="api_set")
]
