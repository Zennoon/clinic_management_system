import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from charges.models import Charge
from patients.models import Patient
from payments.forms import (
    AdjustmentForm,
    ChargePaymentForm,
    PatientPaymentForm,
    PaymentForm,
    UpdatePaymentForm,
    VisitPaymentForm,
)
from payments.models import Payment
from utils import get_url_model_id, payment_details
from visits.models import Visit


# Create your views here.
@login_required
def new_payment_modal(request: HttpRequest):
    form = PaymentForm()
    context = {"form": form}
    response = render(
        request, "payments/partials/new-payment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_payment_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_payment(request: HttpRequest):
    form = PaymentForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "payment")

    if form.is_valid():
        payment = form.save(commit=False)
        payment.acceptor = request.user
        payment.save()
        payment.charge.visit.update_status()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_payment_modal",
                    "message": "Payment created successfully!",
                },
            }
        )
        return response
    else:
        response = render(
            request, "payments/partials/new-payment-modal-partial.html", {"form": form}
        )
        response["HX-Retarget"] = "#new_payment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_payment_modal"}}
        )
        return response


@login_required
def new_charge_payment_modal(request: HttpRequest, id):
    charge = get_object_or_404(Charge, pk=id)
    form = ChargePaymentForm(charge=charge)
    context = {"form": form, "charge": charge}
    response = render(
        request, "payments/partials/new-charge-payment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_charge_payment_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_charge_payment(request: HttpRequest, id):
    charge = get_object_or_404(Charge, pk=id)
    form = ChargePaymentForm(request.POST, charge=charge)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "payment")
    if form.is_valid():
        payment = form.save(commit=False)
        payment.charge = charge
        payment.acceptor = request.user
        payment.save()
        payment.charge.visit.update_status()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_payment_modal",
                    "message": "Payment created successfully!",
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "payments/partials/new-charge-payment-modal-partial.html",
            {"form": form, "charge": charge},
        )
        response["HX-Retarget"] = "#new_charge_payment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_charge_payment_modal"}}
        )
        return response


@login_required
def new_visit_payment_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitPaymentForm(visit=visit)
    context = {"form": form, "visit": visit}
    response = render(
        request, "payments/partials/new-visit-payment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_visit_payment_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_visit_payment(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitPaymentForm(request.POST, visit=visit)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "payment")
    if form.is_valid():
        payment = form.save(commit=False)
        payment.acceptor = request.user
        payment.save()
        payment.charge.visit.update_status()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_visit_payment_modal",
                    "message": "Payment created successfully!",
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "payments/partials/new-visit-payment-modal-partial.html",
            {"form": form, "visit": visit},
        )
        response["HX-Retarget"] = "#new_visit_payment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_visit_payment_modal"}}
        )
        return response


@login_required
def new_patient_payment_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientPaymentForm(patient=patient)
    print(form)
    context = {"form": form, "patient": patient}
    response = render(
        request, "payments/partials/new-patient-payment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_payment_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_patient_payment(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientPaymentForm(request.POST, patient=patient)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "payment")
    if form.is_valid():
        payment = form.save(commit=False)
        payment.acceptor = request.user
        payment.save()
        payment.charge.visit.update_status()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_payment_modal",
                    "message": "Payment created successfully!",
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "payments/partials/new-patient-payment-modal-partial.html",
            {"form": form, "patient": patient},
        )
        response["HX-Retarget"] = "#new_patient_payment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_payment_modal"}}
        )
        return response


@login_required
def update_payment_modal(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    form = PaymentForm(
        instance=payment,
        user=request.user
    )
    context = {"form": form, "payment": payment}
    response = render(
        request, "payments/partials/update-payment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "update_payment_modal"}}
        )
    return response


@login_required
@require_POST
def update_payment(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    form = PaymentForm(request.POST, instance=payment)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "payment")

    if form.is_valid():
        payment = form.save()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "update_payment_modal",
                    "message": "Payment updated successfully!",
                },
            }
        )
        return response
        response = render(
            request,
            "staff/admin/payments/partials/payments-table-row-partial.html",
            {"payment": payment},
        )
        response["HX-Trigger"] = "update-payment-success"
        response["HX-Retarget"] = f"#payments-table-row-id-{payment.id}"
        response["HX-Reswap"] = "outerHTML"
        return response
    else:
        response = render(
            request,
            "payments/partials/update-payment-modal-partial.html",
            {"form": form, "payment": payment},
        )
        response["HX-Retarget"] = "#update_payment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "update_payment_modal"}}
        )
        return response


@login_required
def new_adjustment_modal(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    form = AdjustmentForm(payment=payment)
    context = {"form": form, "payment": payment}
    response = render(
        request, "payments/partials/new-adjustment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_adjustment_modal"}}
        )
    return response


@login_required
def register_new_adjustment(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    form = AdjustmentForm(request.POST, payment=payment)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "payment")

    if form.is_valid():
        adjustment = form.save(commit=False)
        adjustment.payment = payment
        adjustment.created_by = request.user
        adjustment.save()
        payment.charge.visit.update_status()
        response = HttpResponse()
        details_url = payment_details(request, payment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=payment.charge.visit.patient,
                            visit=payment.charge.visit,
                            charge=payment.charge,
                            payment=payment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_adjustment_modal",
                    "message": "Adjustment created successfully!",
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "payments/partials/new-adjustment-modal-partial.html",
            {"form": form, "payment": payment},
        )
        response["HX-Retarget"] = "#new_adjustment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_adjustment_modal"}}
        )
        return response


@login_required
def delete_payment_modal(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    context = {"payment": payment}
    return render(
        request, "payments/partials/delete-payment-modal-partial.html", context
    )


@login_required
@require_POST
def delete_payment(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    payment.is_active = False
    payment.save()
    response = render(
        request,
        "staff/admin/payments/partials/payments-table-row-partial.html",
        {"payment": payment},
    )
    response["HX-Trigger"] = "delete-payment-success"
    response["HX-Retarget"] = f"#payments-table-row-id-{payment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def restore_payment_modal(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    context = {"payment": payment}
    return render(
        request, "payments/partials/restore-payment-modal-partial.html", context
    )


@login_required
@require_POST
def restore_payment(request: HttpRequest, id: int):
    payment = get_object_or_404(Payment, pk=id)
    payment.is_active = True
    payment.save()
    response = render(
        request,
        "staff/admin/payments/partials/payments-table-row-partial.html",
        {"payment": payment},
    )
    response["HX-Trigger"] = "restore-payment-success"
    response["HX-Retarget"] = f"#payments-table-row-id-{payment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def get_patient_visits(request: HttpRequest):
    patient_id = request.GET.get("patient")
    patient = get_object_or_404(Patient, pk=patient_id)
    form = PatientPaymentForm(patient=patient)
    response = HttpResponse(form["visit"])
    response["HX-Trigger-After-Settle"] = json.dumps(
        {"trigger-change": {"id": "id_visit"}}
    )
    return response


@login_required
def get_visit_charges(request: HttpRequest):
    visit_id = request.GET.get("visit")
    visit = get_object_or_404(Visit, pk=visit_id)
    print(visit)
    form = VisitPaymentForm(visit=visit)
    print(form)
    return HttpResponse(form["charge"])
