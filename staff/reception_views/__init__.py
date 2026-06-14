from .reception_dashboard_views import reception_dashboard_urlpatterns
from .reception_patients_views import reception_patients_urlpatterns
from .reception_visits_views import reception_visits_urlpatterns
from .reception_charges_views import reception_charges_urlpatterns
from .reception_payments_views import reception_payments_urlpatterns

reception_urlpatterns = [
    *reception_dashboard_urlpatterns,
    *reception_patients_urlpatterns,
    *reception_visits_urlpatterns,
    *reception_charges_urlpatterns,
    *reception_payments_urlpatterns,
]
