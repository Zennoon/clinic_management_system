from django.urls import path
from . import views

app_name = "appointments"
urlpatterns = [
    path(
        "new_appointment_modal/",
        views.new_appointment_modal,
        name="new_appointment_modal",
    ),
    path(
        "register_new_appointment/",
        views.register_new_appointment,
        name="register_new_appointment",
    ),
    path("get_patient_visits/", views.get_patient_visits, name="get_patient_visits"),
    path(
        "update_appointment_modal/<int:id>/",
        views.update_appointment_modal,
        name="update_appointment_modal",
    ),
    path(
        "update_appointment/<int:id>",
        views.update_appointment,
        name="update_appointment",
    ),
    path(
        "delete_appointment_modal/<int:id>",
        views.delete_appointment_modal,
        name="delete_appointment_modal",
    ),
    path(
        "delete_appointment/<int:id>",
        views.delete_appointment,
        name="delete_appointment",
    ),
    path(
        "restore_appointment_modal/<int:id>",
        views.restore_appointment_modal,
        name="restore_appointment_modal",
    ),
    path(
        "restore_appointment/<int:id>",
        views.restore_appointment,
        name="restore_appointment",
    ),
]
