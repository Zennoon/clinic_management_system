from .auth_views import auth_urlpatterns
from .admin_views import admin_urlpatterns
from .reception_views import reception_urlpatterns
from .nurse_views import nurse_urlpatterns

app_name = "staff"
urlpatterns = [
    *auth_urlpatterns,
    *admin_urlpatterns,
    *reception_urlpatterns,
    *nurse_urlpatterns,
]
