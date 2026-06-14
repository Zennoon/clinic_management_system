from django.urls import path
from . import views

app_name = "charges"
urlpatterns = [
    path("new_charge_modal/", views.new_charge_modal, name="new_charge_modal"),
    path("register_new_charge/", views.register_new_charge, name="register_new_charge"),
    path(
        "new_visit_charge_modal/<int:id>",
        views.new_visit_charge_modal,
        name="new_visit_charge_modal",
    ),
    path(
        "register_new_visit_charge/<int:id>",
        views.register_new_visit_charge,
        name="register_new_visit_charge",
    ),
    path(
        "new_patient_charge_modal/<int:id>",
        views.new_patient_charge_modal,
        name="new_patient_charge_modal",
    ),
    path(
        "register_new_patient_charge/<int:id>",
        views.register_new_patient_charge,
        name="register_new_patient_charge",
    ),
    path("get_patient_visits/", views.get_patient_visits, name="get_patient_visits"),
    path(
        "update_charge_modal/<int:id>",
        views.update_charge_modal,
        name="update_charge_modal",
    ),
    path("update_charge/<int:id>/", views.update_charge, name="update_charge"),
    path(
        "delete_charge_modal/<int:id>",
        views.delete_charge_modal,
        name="delete_charge_modal",
    ),
    path("delete_charge/<int:id>/", views.delete_charge, name="delete_charge"),
    path(
        "restore_charge_modal/<int:id>",
        views.restore_charge_modal,
        name="restore_charge_modal",
    ),
    path("restore_charge/<int:id>/", views.restore_charge, name="restore_charge"),
]
