from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.urls import path

from staff.utils import user_has_role
from staff.forms import ClinicSettingsForm, StaffForm
from staff.models import Staff


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_settings(request: HttpRequest):
    form = ClinicSettingsForm()
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/admin/settings/partials/settings-partial.html",
            {"form": form},
        )
    else:
        return render(request, "staff/admin/settings/page.html", {"form": form})


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
@require_POST
def admin_settings_update(request: HttpRequest):
    form = ClinicSettingsForm(request.POST)
    if form.is_valid():
        form.save_settings()
        response = HttpResponse()
        response["HX-Trigger"] = "update-settings-success"
        return response
    else:
        response = render(
            request,
            "staff/admin/settings/partials/settings-form-partial.html",
            {"form": form},
        )
        response["HX-Reswap"] = "#system_settings_form"
        return response


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_staff_management(request: HttpRequest):
    context = {
        "staff_members": Staff.objects.order_by("id").all(),
        "staff_roles": Staff.RoleEnum.choices,
        "order_options": {"id": "ID", "username": "Username", "date": "Date"},
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/admin/staff-management/partials/staff-management-partial.html",
            context,
        )
    else:
        return render(request, "staff/admin/staff-management/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_staff_filter(request: HttpRequest):
    pass


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def new_staff_modal(request: HttpRequest):
    form = StaffForm()
    context = {"form": form}
    return render(
        request,
        "staff/admin/staff-management/partials/new-staff-modal-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
@require_POST
def register_new_staff(request: HttpRequest):
    form = StaffForm(request.POST)
    if form.is_valid():
        staff = form.save()
        response = render(
            request,
            "staff/admin/staff-management/partials/staff-table-row-partial.html",
            {"staff": staff},
        )
        response["HX-Trigger"] = "new-staff-success"
        return response
    else:
        response = render(
            request,
            "staff/admin/staff-management/partials/new-staff-modal-partial.html",
            {"form": form},
        )
        response["HX-Retarget"] = "#new_staff_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-staff-fail"
        return response


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def update_staff_modal(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    form = StaffForm(instance=staff, initial={"id": id})
    context = {"form": form, "staff": staff}
    return render(
        request,
        "staff/admin/staff-management/partials/update-staff-modal-partial.html",
        context,
    )


@login_required
@require_POST
def update_staff(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    form = StaffForm(request.POST, instance=staff, initial={"id": id})
    if form.is_valid():
        staff = form.save()
        response = render(
            request,
            "staff/admin/staff-management/partials/staff-table-row-partial.html",
            {"staff": staff},
        )
        response["HX-Trigger"] = "update-staff-success"
        response["HX-Retarget"] = f"#staff-table-row-id-{staff.id}"
        response["HX-Reswap"] = "outerHTML"
        return response
    else:
        response = render(
            request,
            "staff/admin/staff-management/partials/update-staff-modal-partial.html",
            {"form": form, "staff": staff},
        )
        response["HX-Retarget"] = "#update_staff_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-staff-fail"
        return response


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def archive_staff_modal(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    context = {"staff": staff}
    return render(
        request,
        "staff/admin/staff-management/partials/archive-staff-modal-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def archive_staff(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    staff.is_active = False
    staff.save()
    response = render(
        request,
        "staff/admin/staff-management/partials/staff-table-row-partial.html",
        {"staff": staff},
    )
    response["HX-Trigger"] = "archive-staff-success"
    response["HX-Retarget"] = f"#staff-table-row-id-{staff.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def restore_staff_modal(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    context = {"staff": staff}
    return render(
        request,
        "staff/admin/staff-management/partials/restore-staff-modal-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
@require_POST
def restore_staff(request: HttpRequest, id: int):
    staff = get_object_or_404(Staff, pk=id)
    staff.is_active = True
    staff.save()
    response = render(
        request,
        "staff/admin/staff-management/partials/staff-table-row-partial.html",
        {"staff": staff},
    )
    response["HX-Trigger"] = "restore-staff-success"
    response["HX-Retarget"] = f"#staff-table-row-id-{staff.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


admin_system_urlpatterns = [
    path("admin/settings/", admin_settings, name="admin_settings"),
    path(
        "admin/settings/update",
        admin_settings_update,
        name="admin_settings_update",
    ),
    path(
        "admin/staff_management",
        admin_staff_management,
        name="admin_staff_management",
    ),
    path("admin/staff/filter/", admin_staff_filter, name="admin_staff_filter"),
    path("new_staff_modal/", new_staff_modal, name="new_staff_modal"),
    path("register_new_staff/", register_new_staff, name="register_new_staff"),
    path(
        "update_staff_modal/<int:id>",
        update_staff_modal,
        name="update_staff_modal",
    ),
    path("update_staff/<int:id>/", update_staff, name="update_staff"),
    path(
        "archive_staff_modal/<int:id>",
        archive_staff_modal,
        name="archive_staff_modal",
    ),
    path("archive_staff/<int:id>/", archive_staff, name="archive_staff"),
    path(
        "restore_staff_modal/<int:id>",
        restore_staff_modal,
        name="restore_staff_modal",
    ),
    path("restore_staff/<int:id>/", restore_staff, name="restore_staff"),
]
