from django import forms
from django.contrib.auth.forms import UserCreationForm


class PlUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nazwa użytkownika"
        self.fields["username"].help_text = (
            "Wymagane. Do 150 znaków. Litery, cyfry i znaki @/./+/-/_."
        )
        self.fields["password1"].label = "Hasło"
        self.fields["password1"].help_text = ""
        self.fields["password2"].label = "Powtórz hasło"
        self.fields["password2"].help_text = "Wpisz to samo hasło co wyżej."
