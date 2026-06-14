from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib.auth import authenticate, login, logout

from .forms import LoginForm


@require_GET
@user_passes_test(
    lambda user: not user.is_authenticated, login_url="/", redirect_field_name=""
)
def login_view(request: HttpRequest):
    form = LoginForm()
    return render(request, "staff/login.html", {"form": form})


@require_POST
def attempt_login(request: HttpRequest):
    form = LoginForm(request.POST)
    if form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password"),
        )
        if user and user.is_active:
            login(request, user)
            response = HttpResponse()
            response["HX-Redirect"] = reverse("index")
            return response
        else:
            return render(
                request,
                "partials/login-form.html",
                {"form": form, "error": "Incorrect login credentials"},
            )
    else:
        return render(request, "partials/login-form.html", {"form": form})


@login_required
def attempt_logout(request: HttpRequest):
    logout(request)
    return redirect(reverse("staff:login"))


auth_urlpatterns = [
    path("login/", login_view, name="login"),
    path("attempt_login/", attempt_login, name="attempt_login"),
    path("attempt_logout/", attempt_logout, name="attempt_logout"),
]
