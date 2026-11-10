from django.urls import path
from . import views

app_name = "vital_signs"
urlpatterns = [
    path("new_visit_vital_sign_modal/<int:id>", views.new_visit_vital_sign_modal, name="new_visit_vital_sign_modal"),
    path("register_new_visit_vital_sign/<int:id>", views.register_new_visit_vital_sign, name="register_new_visit_vital_sign"),
    path("new_patient_vital_sign_modal/<int:id>", views.new_patient_vital_sign_modal, name="new_patient_vital_sign_modal"),
    path("register_new_patient_vital_sign/<int:id>", views.register_new_patient_vital_sign, name="register_new_patient_vital_sign"),
]