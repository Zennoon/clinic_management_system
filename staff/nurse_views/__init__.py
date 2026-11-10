from .nurse_dashboard_views import nurse_dashboard_urlpatterns
from .nurse_vital_signs_views import nurse_vital_signs_urlpatterns
from .nurse_patients_views import nurse_patients_urlpatterns

nurse_urlpatterns = [
    *nurse_dashboard_urlpatterns,
    *nurse_vital_signs_urlpatterns,
    *nurse_patients_urlpatterns,
]