from django.urls import path
from . import views

app_name = "staff"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("attempt_login/", views.attempt_login, name="attempt_login"),
    path("attempt_logout/", views.attempt_logout, name="attempt_logout"),
    path("admin/", views.admin, name="admin"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/dashboard/timespan", views.admin_dashboard_timespan, name="admin_dashboard_timespan"),
    path("admin/activity/", views.admin_activity, name="admin_activity"),
    path("admin/activity/recent_visits", views.admin_activity_recent_visits, name="admin_activity_recent_visits"),
    path("admin/activity/recent_patients", views.admin_activity_recent_patients, name="admin_activity_recent_patients"),
    path("admin/activity/recent_lab_requests", views.admin_activity_recent_lab_requests, name="admin_activity_recent_lab_requests"),
    path("admin/activity/recent_charges", views.admin_activity_recent_charges, name="admin_activity_recent_charges"),
    path("admin/activity/recent_payments", views.admin_activity_recent_payments, name="admin_activity_recent_payments")
]
