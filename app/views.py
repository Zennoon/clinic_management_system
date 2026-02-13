from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from staff.models import Staff

@login_required
def index(request: HttpRequest):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        return redirect(reverse("staff:admin"))
    elif role == Staff.RoleEnum.DOCTOR:
        return redirect(reverse("staff:doctor_dashboard"))
    elif role == Staff.RoleEnum.LABORATORY:
        return redirect(reverse("staff:lab_dashboard"))
    elif role == Staff.RoleEnum.NURSE:
        return redirect(reverse("staff:nurse_dashboard"))
    elif role == Staff.RoleEnum.RECEPTION:
        return redirect(reverse("staff:reception_dashboard"))
    return redirect("index")
