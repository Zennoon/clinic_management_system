from django.urls import path
from . import views

app_name = "payments"
urlpatterns = [
    path("new_payment_modal/", views.new_payment_modal, name="new_payment_modal"),
    path(
        "register_new_payment/", views.register_new_payment, name="register_new_payment"
    ),
    path(
        "new_charge_payment_modal/<int:id>/",
        views.new_charge_payment_modal,
        name="new_charge_payment_modal",
    ),
    path(
        "register_new_charge_payment/<int:id>/",
        views.register_new_charge_payment,
        name="register_new_charge_payment",
    ),
    path(
        "new_visit_payment_modal/<int:id>/",
        views.new_visit_payment_modal,
        name="new_visit_payment_modal",
    ),
    path(
        "register_new_visit_payment/<int:id>/",
        views.register_new_visit_payment,
        name="register_new_visit_payment",
    ),
    path(
        "new_patient_payment_modal/<int:id>/",
        views.new_patient_payment_modal,
        name="new_patient_payment_modal",
    ),
    path(
        "register_new_patient_payment/<int:id>/",
        views.register_new_patient_payment,
        name="register_new_patient_payment",
    ),
    path(
        "new_adjustment_modal/<int:id>/", views.new_adjustment_modal, name="new_adjustment_modal"
    ),
    path(
        "register_new_adjustment/<int:id>/",
        views.register_new_adjustment,
        name="register_new_adjustment",
    ),
    path("get_patient_visits/", views.get_patient_visits, name="get_patient_visits"),
    path("get_visit_charges/", views.get_visit_charges, name="get_visit_charges"),
    path(
        "update_payment_modal/<int:id>/",
        views.update_payment_modal,
        name="update_payment_modal",
    ),
    path("update_payment/<int:id>/", views.update_payment, name="update_payment"),
    path(
        "delete_payment_modal/<int:id>/",
        views.delete_payment_modal,
        name="delete_payment_modal",
    ),
    path("delete_payment/<int:id>/", views.delete_payment, name="delete_payment"),
    path(
        "restore_payment_modal/<int:id>/",
        views.restore_payment_modal,
        name="restore_payment_modal",
    ),
    path("restore_payment/<int:id>/", views.restore_payment, name="restore_payment"),
]
