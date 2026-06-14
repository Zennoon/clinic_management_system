from .admin_core_views import admin_core_urlpatterns
from .admin_clinical_views import admin_clinical_urlpatterns
from .admin_financial_views import admin_financial_urlpatterns
from .admin_tests_views import admin_tests_urlpatterns
from .admin_system_views import admin_system_urlpatterns

admin_urlpatterns = [
    *admin_core_urlpatterns,
    *admin_clinical_urlpatterns,
    *admin_financial_urlpatterns,
    *admin_tests_urlpatterns,
    *admin_system_urlpatterns,
]
