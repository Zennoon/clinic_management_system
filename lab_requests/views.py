from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from lab_requests.forms import LabGroupForm, LabGroupObservationForm, LabObservationForm
from lab_requests.models import LabObservation, LabGroup

# Create your views here.
@login_required
def new_lab_group_modal(request: HttpRequest):
    form = LabGroupForm()
    context = { "form": form }
    return render(request, "lab_requests/partials/new-lab-group-modal-partial.html", context)

@login_required
@require_POST
def register_new_lab_group(request: HttpRequest):
    form = LabGroupForm(request.POST)
    if form.is_valid():
        lab_group = form.save(commit=False)
        lab_group.created_by = request.user
        lab_group.save()
        response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-partial.html", context={ "lab_group": lab_group })
        response["HX-Trigger"] = "new-lab-group-success"
        return response
    else:
        response = render(request, "lab_requests/partials/new-lab-group-modal-partial.html", { "form": form })
        response["HX-Retarget"] = "#new_lab_group_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-lab-group-fail"
        return response

@login_required
def new_lab_group_observation_modal(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    form = LabGroupObservationForm(lab_group=lab_group)
    return render(request, "lab_requests/partials/new-lab-group-observation-modal-partial.html", context={ "form": form, "lab_group": lab_group })

@login_required
@require_POST
def register_new_lab_group_observation(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    form = LabGroupObservationForm(request.POST, lab_group=lab_group)
    if form.is_valid():
        lab_observation = form.save(commit=False)
        lab_observation.lab_group = lab_group
        lab_observation.created_by = request.user
        lab_observation.save()
        response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-observation-partial.html", context={ "observation": lab_observation })
        response["HX-Trigger"] = "new-lab-group-observation-success"
        return response
    else:
        response = render(request, "lab_requests/partials/new-lab-group-observation-modal-partial.html", { "form": form, "lab_group": lab_group })
        response["HX-Retarget"] = "#new_lab_group_observation_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-lab-group-observation-fail"
        return response

@login_required
def update_lab_group_modal(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    form = LabGroupForm(instance=lab_group)
    context = { "form": form, "lab_group": lab_group }
    return render(request, "lab_requests/partials/update-lab-group-modal-partial.html", context)


@login_required
@require_POST
def update_lab_group(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    form = LabGroupForm(request.POST, instance=lab_group)
    if form.is_valid():
        lab_group = form.save()
        response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-partial.html", context={ "lab_group": lab_group })
        response["HX-Trigger"] = "update-lab-group-success"
        return response
    else:
        response = render(request, "lab_requests/partials/update-lab-group-modal-partial.html", { "form": form, "lab_group": lab_group })
        response["HX-Retarget"] = "#update_lab_group_modal"
        response["HX-Trigger-After-Settle"] = "update-lab-group-fail"
        return response

@login_required
def archive_lab_group_modal(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    context = { "lab_group": lab_group }
    return render(request, "lab_requests/partials/archive-lab-group-modal-partial.html", context)

@login_required
@require_POST
def archive_lab_group(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    lab_group.is_active = False
    for observation in lab_group.observations.all():
        if observation.is_active:
            observation.is_active = False
            observation.save()
    lab_group.save()
    response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-partial.html", { "lab_group": lab_group })
    response["HX-Trigger"] = "archive-lab-group-success"
    return response

@login_required
def restore_lab_group_modal(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    context = { "lab_group": lab_group }
    return render(request, "lab_requests/partials/restore-lab-group-modal-partial.html", context)

@login_required
@require_POST
def restore_lab_group(request: HttpRequest, id: int):
    lab_group = get_object_or_404(LabGroup, pk=id)
    lab_group.is_active = True
    for observation in lab_group.observations.all():
        if not observation.is_active:
            observation.is_active = True
            observation.save()
    lab_group.save()
    response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-partial.html", { "lab_group": lab_group })
    response["HX-Trigger"] = "restore-lab-group-success"
    return response

@login_required
def update_lab_group_observation_modal(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    form = UpdateLabGroupObservationForm(instance=lab_observation)
    context = { "form": form, "observation": lab_observation }
    return render(request, "lab_requests/partials/update-lab-group-observation-modal-partial.html", context)

@login_required
@require_POST
def update_lab_group_observation(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    form = UpdateLabGroupObservationForm(request.POST, instance=lab_observation)
    if form.is_valid():
        lab_observation = form.save()
        context = {
            "tests": LabGroup.objects.all()
        }
        response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-partial.html", context)
        response["HX-Trigger"] = "update-lab-group-observation-success"
        return response
    else:
        response = render(request, "lab_requests/partials/update-lab-group-observation-modal-partial.html", { "form": form, "observation": lab_observation })
        response["HX-Retarget"] = "#update_lab_group_observation_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-lab-group-observation-fail"
        return response

@login_required
def archive_lab_group_observation_modal(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    context = { "observation": lab_observation }
    return render(request, "lab_requests/partials/archive-lab-group-observation-modal-partial.html", context)

@login_required
@require_POST
def archive_lab_group_observation(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    lab_observation.is_active = False
    lab_observation.save()
    response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-observation-partial.html", context={ "observation": lab_observation })
    response["HX-Trigger"] = "archive-lab-group-observation-success"
    return response

@login_required
def restore_lab_group_observation_modal(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    context = { "observation": lab_observation }
    return render(request, "lab_requests/partials/restore-lab-group-observation-modal-partial.html", context)

@login_required
@require_POST
def restore_lab_group_observation(request: HttpRequest, id: int):
    lab_observation = get_object_or_404(LabObservation, pk=id)
    lab_observation.is_active = True
    lab_observation.save()
    response = render(request, "staff/admin/tests-configuration/partials/tests-configuration-group-observation-partial.html", context={ "observation": lab_observation })
    response["HX-Trigger"] = "restore-lab-group-observation-success"
    return response
