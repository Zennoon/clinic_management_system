from django.urls import path
from . import views

app_name = "visits"
urlpatterns = [
    path("new_visit_modal", views.new_visit_modal, name="new_visit_modal"),
    path("register_new_visit", views.register_new_visit, name="register_new_visit"),
    path("update_visit_modal/<int:id>", views.update_visit_modal, name="update_visit_modal"),
    path("update_visit/<int:id>", views.update_visit, name="update_visit"),
    path("delete_visit_modal/<int:id>", views.delete_visit_modal, name="delete_visit_modal"),
    path("delete_visit/<int:id>", views.delete_visit, name="delete_visit"),
    path("restore_visit_modal/<int:id>", views.restore_visit_modal, name="restore_visit_modal"),
    path("restore_visit/<int:id>", views.restore_visit, name="restore_visit"),
]
