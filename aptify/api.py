from ninja import NinjaAPI, Router
from assignments.api import router as assignments_router
from analysis.api import router as analysis_router

# ... (init code)

api = NinjaAPI(
    title="AptiFy API",
    version="1.0.0",
    description="API for AptiFy Academic Intelligence Platform"
)

api.add_router("/assignments", assignments_router)
api.add_router("/analysis", analysis_router)

# Authentication placeholder
def django_auth(request):
    if request.user.is_authenticated:
        return request.user
    return None
