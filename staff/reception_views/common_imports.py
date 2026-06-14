import json
from decimal import Decimal

from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce, Concat
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, path, re_path
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..utils import clean_urlencode, format_timedelta, user_has_role

from appointments.models import Appointment
from charges.models import Charge
from patients.models import Patient
from payments.models import Payment
from staff.models import Staff
from visits.models import Visit

