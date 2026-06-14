import json
from decimal import Decimal

from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils import timezone
from ..utils import format_timedelta, user_has_role

from appointments.models import Appointment
from charges.models import Charge
from payments.models import Payment
from staff.models import Staff
from visits.models import Visit


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception(_: HttpRequest):
    return redirect(reverse("staff:reception_dashboard"))


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_dashboard(request: HttpRequest):
    # Pulse
    today = timezone.now().date()
    total_visits_today_count = Visit.objects.filter(date__date=today).count()
    total_in_clinic_count = Visit.objects.filter(
        Q(date__date=today)
        & ~Q(visit_status=Visit.VisitStatusEnum.COMPLETED)
        & ~Q(visit_status=Visit.VisitStatusEnum.CANCELLED)
        & ~Q(visit_status=Visit.VisitStatusEnum.STALE)
    ).count()
    awaiting_consultation_payment_count = Visit.objects.filter(
        Q(date__date=today)
        & Q(visit_status=Visit.VisitStatusEnum.AWAITING_CONSULTATION_PAYMENT)
    ).count()
    awaiting_lab_payment_count = Visit.objects.filter(
        Q(date__date=today) & Q(visit_status=Visit.VisitStatusEnum.AWAITING_LAB_PAYMENT)
    ).count()
    awaiting_consultation_count = Visit.objects.filter(
        Q(date__date=today)
        & Q(visit_status=Visit.VisitStatusEnum.AWAITING_CONSULTATION)
    ).count()
    todays_appointments_count = Appointment.objects.filter(
        Q(appointment_date__date=today) & Q(checked_in=False)
    ).count()

    # Finance
    total_services_charged_today = Charge.objects.filter(date__date=today).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    total_money_collected = Payment.objects.filter(
        Q(date__date=today)
        & ~Q(payment_method=Payment.PaymentMethodEnum.WAIVER)
        & ~Q(payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    todays_charges_money_collected = Payment.objects.filter(
        Q(date__date=today)
        & Q(charge__date__date=today)
        & ~Q(payment_method=Payment.PaymentMethodEnum.WAIVER)
        & ~Q(payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    grace_period_amount = Payment.objects.filter(
        Q(date__date=today) & Q(payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    waived_amount = Payment.objects.filter(
        Q(date__date=today) & Q(payment_method=Payment.PaymentMethodEnum.WAIVER)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    debt_amount_today = (
        Charge.objects.filter(date__date=today)
        .annotate(paid_amount=Coalesce(Sum("payments__amount"), Value(Decimal("0.00"))))
        .aggregate(
            total=Coalesce(Sum(F("amount") - F("paid_amount")), Value(Decimal("0.00")))
        )["total"]
    )

    charges_by_type = (
        Charge.objects.filter(date__date=today)
        .values("charge_type")
        .annotate(total_amount=Sum("amount"))
        .order_by("-total_amount")
    )

    charge_type_breakdown = []
    for item in charges_by_type:
        percentage = (
            (item["total_amount"] * 100 / total_services_charged_today)
            if total_services_charged_today > 0
            else 0
        )
        charge_type_breakdown.append(
            {
                "type": item["charge_type"],
                "amount": item["total_amount"],
                "percentage": percentage,
            }
        )

    payment_amount_by_method = (
        Payment.objects.filter(Q(date__date=today))
        .values("payment_method")
        .annotate(total_amount=Sum("amount"))
        .order_by("-total_amount")
    )
    payment_method_breakdown = []
    for item in payment_amount_by_method:
        percentage = (
            (item["total_amount"] * 100 / total_money_collected)
            if total_money_collected > 0
            else 0
        )
        payment_method_breakdown.append(
            {
                "method": item["payment_method"],
                "amount": item["total_amount"],
                "percentage": percentage,
            }
        )

    # Efficiency
    longest_waiting_visits = (
        Visit.objects.filter(
            Q(date__date=today)
            & ~Q(visit_status=Visit.VisitStatusEnum.COMPLETED)
            & ~Q(visit_status=Visit.VisitStatusEnum.CANCELLED)
            & ~Q(visit_status=Visit.VisitStatusEnum.STALE)
        )
        .annotate(waiting_time=timezone.now() - F("current_status_since"))
        .order_by("-waiting_time")[:5]
    )
    for visit in longest_waiting_visits:
        visit.formatted_waiting_time = format_timedelta(visit.waiting_time)

    # Context
    context = {
        "total_visits_today_count": total_visits_today_count,
        "total_in_clinic_count": total_in_clinic_count,
        "awaiting_consultation_payment_count": awaiting_consultation_payment_count,
        "awaiting_lab_payment_count": awaiting_lab_payment_count,
        "awaiting_consultation_count": awaiting_consultation_count,
        "todays_appointments_count": todays_appointments_count,
        "total_services_charged_today": total_services_charged_today,
        "total_money_collected": total_money_collected,
        "todays_charges_money_collected": todays_charges_money_collected,
        "grace_period_amount": grace_period_amount,
        "waived_amount": waived_amount,
        "debt_amount_today": debt_amount_today,
        "charge_type_breakdown": charge_type_breakdown,
        "payment_method_breakdown": payment_method_breakdown,
        "longest_waiting_visits": longest_waiting_visits,
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/reception/dashboard/partials/dashboard-partial.html",
            context,
        )
    else:
        return render(request, "staff/reception/dashboard/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_dashboard_longest_waiting_visits(request: HttpRequest):
    longest_waiting_visits = (
        Visit.objects.filter(
            Q(date__date=timezone.now().date())
            & ~Q(visit_status=Visit.VisitStatusEnum.COMPLETED)
            & ~Q(visit_status=Visit.VisitStatusEnum.CANCELLED)
            & ~Q(visit_status=Visit.VisitStatusEnum.STALE)
        )
        .annotate(waiting_time=timezone.now() - F("current_status_since"))
        .order_by("-waiting_time")[:5]
    )
    for visit in longest_waiting_visits:
        visit.formatted_waiting_time = format_timedelta(visit.waiting_time)

    return render(
        request,
        "staff/reception/dashboard/partials/dashboard-longest-waiting-visits-table-body-partial.html",
        {"longest_waiting_visits": longest_waiting_visits},
    )

reception_dashboard_urlpatterns = [
    path("reception/", reception, name="reception"),
    path("reception/dashboard/", reception_dashboard, name="reception_dashboard"),
    path(
        "reception/dashboard/longest_waiting_visits/",
        reception_dashboard_longest_waiting_visits,
        name="reception_dashboard_longest_waiting_visits",
    ),
]