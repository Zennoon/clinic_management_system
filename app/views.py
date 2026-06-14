from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from staff.models import Staff


@login_required
def index(request: HttpRequest):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        return redirect(reverse("staff:admin_dashboard"))
    elif role == Staff.RoleEnum.DOCTOR:
        return redirect(reverse("staff:doctor_dashboard"))
    elif role == Staff.RoleEnum.LABORATORY:
        return redirect(reverse("staff:lab_dashboard"))
    elif role == Staff.RoleEnum.NURSE:
        return redirect(reverse("staff:nurse_dashboard"))
    elif role == Staff.RoleEnum.RECEPTION:
        return redirect(reverse("staff:reception_dashboard"))
    return redirect("index")


@login_required
def patient_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        return redirect(reverse("staff:admin_patient_details"), id=id)
    elif role == Staff.RoleEnum.DOCTOR:
        return redirect(reverse("staff:doctor_patient_details"), id=id)
    elif role == Staff.RoleEnum.LABORATORY:
        return redirect(reverse("staff:lab_patient_details"), id=id)
    elif role == Staff.RoleEnum.NURSE:
        return redirect(reverse("staff:nurse_patient_details"), id=id)
    elif role == Staff.RoleEnum.RECEPTION:
        return redirect(reverse("staff:reception_patient_details", args=[id]))
    return redirect("index")


@login_required
def visit_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        return redirect(reverse("staff:admin_visit_details"), id=id)
    elif role == Staff.RoleEnum.DOCTOR:
        return redirect(reverse("staff:doctor_visit_details"), id=id)
    elif role == Staff.RoleEnum.LABORATORY:
        return redirect(reverse("staff:lab_visit_details"), id=id)
    elif role == Staff.RoleEnum.NURSE:
        return redirect(reverse("staff:nurse_visit_details"), id=id)
    elif role == Staff.RoleEnum.RECEPTION:
        return redirect(reverse("staff:reception_visit_details", args=[id]))
    return redirect("index")


@login_required
def charge_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        url = reverse("staff:admin_charge_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.DOCTOR:
        url = reverse("staff:doctor_charge_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.LABORATORY:
        url = reverse("staff:lab_charge_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.NURSE:
        url = reverse("staff:nurse_charge_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.RECEPTION:
        url = reverse("staff:reception_charge_details", kwargs={"id": id})
    else:
        url = reverse("index")

    if request.headers.get("HX-Request"):
        response = HttpResponse()
        response["Hx-Location"] = { "path": url, "replace": url }
        return response

    return redirect(url)
