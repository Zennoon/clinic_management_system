from django.urls import path
from . import views

app_name = "patients"
urlpatterns = [
    path("new_patient_modal/", views.new_patient_modal, name="new_patient_modal"),
    path("new_patient/", views.register_new_patient, name="register_new_patient"),
    path("update_patient_modal/<int:id>", views.update_patient_modal, name="update_patient_modal"),
    path("update_patient", views.update_patient, name="update_patient"),
    path("delete_patient_modal/<int:id>", views.delete_patient_modal, name="delete_patient_modal"),
    path("delete_patient/<int:id>", views.delete_patient, name="delete_patient"),
    path("restore_patient_modal/<int:id>", views.restore_patient_modal, name="restore_patient_modal"),
    path("restore_patient/<int:id>", views.restore_patient, name="restore_patient"),
]
