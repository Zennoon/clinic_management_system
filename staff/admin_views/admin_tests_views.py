from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path

from staff.utils import user_has_role
from lab_requests.models import LabGroup
from staff.models import Staff


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_tests_configuration(request: HttpRequest):
    groups = LabGroup.objects.all()
    context = {"groups": groups}
    return render(request, "staff/admin/tests-configuration/page.html", context)


admin_tests_urlpatterns = [
    path(
        "admin/tests_configuration/",
        admin_tests_configuration,
        name="admin_tests_configuration",
    ),
]
