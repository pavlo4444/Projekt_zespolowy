from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("konfigurator/", views.builder_view, name="builder"),
    path("rejestracja/", views.register_view, name="register"),
    path("szukaj/", views.search_view, name="search"),
    path("api/zestaw/", views.api_build_summary, name="api_build"),
    path("api/kategoria/<slug:slug>/", views.api_category_components, name="api_category"),
    path("api/ustaw/", views.api_set_part, name="api_set"),
    path("moje-zestawy/", views.my_builds, name="my_builds"),
    path("moje-zestawy/<int:build_id>/usun/", views.delete_build, name="delete_build"),
    path("api/wyczysc/", views.api_clear_build, name="api_clear"),
    path("api/zapisz/", views.api_save_build, name="api_save")
]
