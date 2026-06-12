from django.urls import path

from . import views

app_name = "builder"
urlpatterns = [
     path("", """views.index""", name="index"),
     path("rejestracja/", """views.register_view""", name="register"),
]
