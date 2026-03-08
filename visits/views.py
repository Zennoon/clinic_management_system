from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from visits.forms import VisitForm
from visits.models import Visit
# Create your views here.

@login_required
def new_visit_modal(request: HttpRequest):
    form = VisitForm()
    context = { "form": form }
    return render(request, "visits/partials/new-visit-modal-partial.html", context)

@login_required
def register_new_visit(request: HttpRequest):
    form = VisitForm(request.POST)
    if form.is_valid():
        visit = form.save()
        response = render(request, "staff/admin/visits/partials/visits-table-row-partial.html", { "visit": visit })
        response["HX-Trigger"] = "new-visit-success"
        return response
    else:
        response = render(request, "visits/partials/new-visit-modal-partial.html", { "form": form })
        response["+HX-Retarget"] = "#new_visit_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-visit-fail"
        return response

@login_required
def update_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitForm(instance=visit)
    context = { "form": form, "visit": visit }
    return render(request, "visits/partials/update-visit-modal-partial.html", context)

@login_required
@require_POST
def update_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitForm(request.POST, instance=visit)
    if form.is_valid():
        visit = form.save()
        response = render(request, "staff/admin/visits/partials/visits-table-row-partial.html", { "visit": visit })
        response["HX-Trigger"] = "update-visit-success"
        response["HX-Retarget"] = f"#visits-table-row-id-{visit.id}"
        response["HX-Reswap"] = "outerHTML"
        return response
    else:
        response = render(request, "visits/partials/update-visit-modal-partial.html", { "form": form })
        response["HX-Retarget"] = "#update_visit_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-visit-fail"
        return response

@login_required
def delete_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    context = { "visit": visit }
    return render(request, "visits/partials/delete-visit-modal-partial.html", context)

@login_required
@require_POST
def delete_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    visit.is_active = False
    visit.save()
    response = render(request, "staff/admin/visits/partials/visits-table-row-partial.html", { "visit": visit }) 
    response["HX-Trigger"] = "delete-visit-success"
    response["HX-Retarget"] = f"#visits-table-row-id-{visit.id}"
    response["HX-Reswap"] = "outerHTML"
    return response

@login_required
def restore_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    context = { "visit": visit }
    return render(request, "visits/partials/restore-visit-modal-partial.html", context)

@login_required
@require_POST
def restore_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    visit.is_active = True
    visit.save()
    response = render(request, "staff/admin/visits/partials/visits-table-row-partial.html", { "visit": visit }) 
    response["HX-Trigger"] = "restore-visit-success"
    response["HX-Retarget"] = f"#visits-table-row-id-{visit.id}"
    response["HX-Reswap"] = "outerHTML"
    return response