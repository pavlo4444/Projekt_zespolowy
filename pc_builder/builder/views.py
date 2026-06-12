import json
from typing import Any

from django.contrib.auth import login
from django.shortcuts import render,redirect
from .forms import PlUserCreationForm
from django.http import HttpRequest, JsonResponse


def index(request: HttpRequest):
    return render(request, "builder/index.html")

def register_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("builder:builder")
    if request.method == "POST":
        form = PlUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("builder:builder")
    else:
        form = PlUserCreationForm()
    return render(request, "registration/register.html", {"form": form})