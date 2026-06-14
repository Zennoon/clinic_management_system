from django.http import HttpRequest
from django.urls import reverse
from django.shortcuts import reverse

from staff.models import Staff


def patient_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        url = reverse("staff:admin_patient_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.DOCTOR:
        url = reverse("staff:doctor_patient_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.LABORATORY:
        url = reverse("staff:lab_patient_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.NURSE:
        url = reverse("staff:nurse_patient_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.RECEPTION:
        url = reverse("staff:reception_patient_details", kwargs={"id": id})
    else:
        url = reverse("index")
    
    return url

def visit_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        url = reverse("staff:admin_visit_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.DOCTOR:
        url = reverse("staff:doctor_visit_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.LABORATORY:
        url = reverse("staff:lab_visit_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.NURSE:
        url = reverse("staff:nurse_visit_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.RECEPTION:
        url = reverse("staff:reception_visit_details", kwargs={"id": id})
    else:
        url = reverse("index")
    
    return url

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
    
    return url

def payment_details(request: HttpRequest, id):
    role = request.user.role
    if role == Staff.RoleEnum.ADMIN:
        url = reverse("staff:admin_payment_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.DOCTOR:
        url = reverse("staff:doctor_payment_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.LABORATORY:
        url = reverse("staff:lab_payment_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.NURSE:
        url = reverse("staff:nurse_payment_details", kwargs={"id": id})
    elif role == Staff.RoleEnum.RECEPTION:
        url = reverse("staff:reception_payment_details", kwargs={"id": id})
    else:
        url = reverse("index")
    
    return url

def get_url_model_id(model, patient=None, visit=None, charge=None, payment=None):
    model_id = None
    match model:
        case "patient":
            model_id = patient.id if patient else None
        case "visit":
            model_id = visit.id if visit else None
        case "charge":
            model_id = charge.id if charge else None
        case "payment":
            model_id = payment.id if payment else None
        case _:
            model_id = None
    
    return str(model_id)