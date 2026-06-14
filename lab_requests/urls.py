from django.urls import path
from . import views

app_name = "lab_requests"
urlpatterns = [
    path("new_lab_group_modal/", views.new_lab_group_modal, name="new_lab_group_modal"),
    path("register_new_lab_group/", views.register_new_lab_group, name="register_new_lab_group"),
    path("new_lab_group_observation_modal/<int:id>/", views.new_lab_group_observation_modal, name="new_lab_group_observation_modal"),
    path("register_new_lab_group_observation/<int:id>/", views.register_new_lab_group_observation, name="register_new_lab_group_observation"),
    path("update_lab_group_modal/<int:id>/", views.update_lab_group_modal, name="update_lab_group_modal"),
    path("update_lab_group/<int:id>/", views.update_lab_group, name="update_lab_group"),
    path("archive_lab_group_modal/<int:id>/", views.archive_lab_group_modal, name="archive_lab_group_modal"),
    path("archive_lab_group/<int:id>/", views.archive_lab_group, name="archive_lab_group"),
    path("restore_lab_group_modal/<int:id>/", views.restore_lab_group_modal, name="restore_lab_group_modal"),
    path("restore_lab_group/<int:id>/", views.restore_lab_group, name="restore_lab_group"),
    path("update_lab_group_observation_modal/<int:id>/", views.update_lab_group_observation_modal, name="update_lab_group_observation_modal"),
    path("update_lab_group_observation/<int:id>/", views.update_lab_group_observation, name="update_lab_group_observation"),
    path("archive_lab_group_observation_modal/<int:id>/", views.archive_lab_group_observation_modal, name="archive_lab_group_observation_modal"),
    path("archive_lab_group_observation/<int:id>/", views.archive_lab_group_observation, name="archive_lab_group_observation"),
    path("restore_lab_group_observation_modal/<int:id>/", views.restore_lab_group_observation_modal, name="restore_lab_group_observation_modal"),
    path("restore_lab_group_observation/<int:id>/", views.restore_lab_group_observation, name="restore_lab_group_observation"),

]
