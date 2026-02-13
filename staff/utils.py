from django.contrib.auth.decorators import user_passes_test
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import timedelta

from charges.models import Charge
from lab_requests.models import LabTestRequest
from staff.models import Staff
from visits.models import Visit

def user_has_role(role: Staff.RoleEnum):
    def decorator(view_func):
        wrapper = user_passes_test(
            lambda u: u.role is role,
            login_url='staff/login',
        )
    
        return wrapper(view_func)
    return decorator

def fill_missing(visit_data: dict) -> dict:
    visit_data["revenue"] = float(visit_data["revenue"] or 0)
    visit_data["previous_revenue"] = float(visit_data["previous_revenue"] or 0)
    visit_data["charges"] = float(visit_data["charges"] or 0)
    visit_data["previous_charges"] = float(visit_data["previous_charges"] or 0)
    visit_data["count_trend"] = (visit_data["count"] - visit_data["previous_count"]) / (
                visit_data["previous_count"] or 1) * 100
    visit_data["revenue_trend"] = float((visit_data["revenue"] - visit_data["previous_revenue"]) / (
                visit_data["previous_revenue"] or 1) * 100)
    visit_data["charges_trend"] = float((visit_data["charges"] - visit_data["previous_charges"]) / (
                visit_data["previous_charges"] or 1) * 100)
    return visit_data

def get_timespan_data(start_date, previous_date, history_start_date, trunc):
    # don't use with_financials() here — its joins can inflate aggregates
    # compute counts and money sums from source relations in separate queries to avoid join inflation
    visit_count = Visit.objects.filter(created_at__gte=start_date).count()
    previous_count = Visit.objects.filter(created_at__gte=previous_date, created_at__lt=start_date).count()
    revenue = Visit.objects.filter(created_at__gte=start_date).aggregate(value=Sum('payments__amount'))['value']
    previous_revenue = Visit.objects.filter(created_at__gte=previous_date, created_at__lt=start_date).aggregate(value=Sum('payments__amount'))['value']

    charges = Visit.objects.filter(created_at__gte=start_date).aggregate(value=Sum('charges__amount'))['value']
    previous_charges = Visit.objects.filter(created_at__gte=previous_date, created_at__lt=start_date).aggregate(value=Sum('charges__amount'))['value']

    visit_data = {
        "count": visit_count,
        "previous_count": previous_count,
        "revenue": revenue,
        "previous_revenue": previous_revenue,
        "charges": charges,
        "previous_charges": previous_charges,
    }
    visit_data = fill_missing(visit_data)

    # build history by computing counts, revenues and charges in separate queries
    counts_qs = (
        Visit.objects
        .filter(created_at__gte=history_start_date)
        .annotate(time=trunc('created_at'))
        .values('time')
        .annotate(count=Count('id'))
        .order_by('time')
    )

    revenue_qs = (
        Visit.objects
        .filter(created_at__gte=history_start_date)
        .annotate(time=trunc('created_at'))
        .values('time')
        .annotate(revenue=Sum('payments__amount'))
        .order_by('time')
    )

    charges_qs = (
        Visit.objects
        .filter(created_at__gte=history_start_date)
        .annotate(time=trunc('created_at'))
        .values('time')
        .annotate(charges=Sum('charges__amount'))
        .order_by('time')
    )

    revenue_map = {r['time']: r['revenue'] for r in revenue_qs}
    charges_map = {c['time']: c['charges'] for c in charges_qs}

    history = []
    for entry in counts_qs:
        t = entry['time']
        history.append({
            "time": t.isoformat(),
            "count": entry.get('count') or 0,
            "revenue": float(revenue_map.get(t) or 0),
            "charges": float(charges_map.get(t) or 0)
        })

    charges_breakdown = (
        Visit.objects
        .filter(created_at__gte=start_date)
        .aggregate(
            consultation=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.CONSULTATION)),
            laboratory=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.LABORATORY)),
            procedure=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.PROCEDURE)),
            medication=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.MEDICATION)),
            other=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.OTHER)),
        )
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["procedure"] = float(charges_breakdown["procedure"] or 0)
    charges_breakdown["medication"] = float(charges_breakdown["medication"] or 0)
    charges_breakdown["other"] = float(charges_breakdown["other"] or 0)

    most_ordered_tests = (
        LabTestRequest.objects
        .filter(created_at__gte=start_date)
        .values('lab_test__id', 'lab_test__name')
        .annotate(order_count=Count('lab_test__id'))
        .order_by('-order_count')[:5]
    )

    return {
        "visit_data": visit_data,
        "history": history,
        "charges_breakdown": charges_breakdown,
        "most_ordered_tests": list(most_ordered_tests),
    }

def get_today_data():
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    return get_timespan_data(
        start_date=today,
        previous_date=yesterday,
        history_start_date=today-relativedelta(days=29),
        trunc=TruncDate
    )

def get_week_data():
    now = timezone.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    previous_week_start = week_start - timedelta(days=7)
    return get_timespan_data(
        start_date=week_start,
        previous_date=previous_week_start,
        history_start_date=week_start-relativedelta(weeks=9),
        trunc=TruncWeek
    )

def get_month_data():
    now = timezone.now()
    today = now.date()
    month_start = today.replace(day=1)
    previous_month_start = month_start - relativedelta(months=1)
    return get_timespan_data(
        start_date=month_start,
        previous_date=previous_month_start,
        history_start_date=month_start-relativedelta(months=9),
        trunc=TruncMonth
    )

def get_year_data():
    now = timezone.now()
    today = now.date()
    year_start = timezone.datetime(today.year, 1, 1, 0, 0, 0, 0)
    previous_year_start = year_start - relativedelta(years=1)
    return get_timespan_data(
        start_date=year_start,
        previous_date=previous_year_start,
        history_start_date=year_start-relativedelta(years=9),
        trunc=TruncYear
    )

def get_all_data():
    visit_count = Visit.objects.count()
    previous_count = visit_count
    revenue = Visit.objects.aggregate(value=Sum('payments__amount'))['value']
    previous_revenue = revenue
    charges = Visit.objects.aggregate(value=Sum('charges__amount'))['value']
    previous_charges = charges

    visit_data = {
        "count": visit_count,
        "previous_count": previous_count,
        "revenue": revenue,
        "previous_revenue": previous_revenue,
        "charges": charges,
        "previous_charges": previous_charges,
    }
    visit_data = fill_missing(visit_data)

    # build history by computing counts, revenues and charges in separate queries
    counts_qs = (
        Visit.objects
        .annotate(time=TruncYear('created_at'))
        .values('time')
        .annotate(count=Count('id'))
        .order_by('time')
    )

    revenue_qs = (
        Visit.objects
        .annotate(time=TruncYear('created_at'))
        .values('time')
        .annotate(revenue=Sum('payments__amount'))
        .order_by('time')
    )

    charges_qs = (
        Visit.objects
        .annotate(time=TruncYear('created_at'))
        .values('time')
        .annotate(charges=Sum('charges__amount'))
        .order_by('time')
    )

    revenue_map = {r['time']: r['revenue'] for r in revenue_qs}
    charges_map = {c['time']: c['charges'] for c in charges_qs}

    history = []
    for entry in counts_qs:
        t = entry['time']
        history.append({
            "time": t.isoformat(),
            "count": entry.get('count') or 0,
            "revenue": float(revenue_map.get(t) or 0),
            "charges": float(charges_map.get(t) or 0)
        })

    charges_breakdown = (
        Visit.objects
        .aggregate(
            consultation=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.CONSULTATION)),
            laboratory=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.LABORATORY)),
            procedure=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.PROCEDURE)),
            medication=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.MEDICATION)),
            other=Sum('charges__amount', filter=Q(charges__charge_type=Charge.ChargeTypeEnum.OTHER)),
        )
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["procedure"] = float(charges_breakdown["procedure"] or 0)
    charges_breakdown["medication"] = float(charges_breakdown["medication"] or 0)
    charges_breakdown["other"] = float(charges_breakdown["other"] or 0)

    most_ordered_tests = (
        LabTestRequest.objects
        .values('lab_test__id', 'lab_test__name')
        .annotate(order_count=Count('lab_test__id'))
        .order_by('-order_count')[:5]
    )

    return {
        "visit_data": visit_data,
        "history": history,
        "charges_breakdown": charges_breakdown,
        "most_ordered_tests": list(most_ordered_tests),
    }