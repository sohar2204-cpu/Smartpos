from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .utils import get_user_store


class StoreScopeMiddleware:
    """
    Runs on every request after authentication.
    Attaches request.store from the logged-in user's UserProfile.
    Blocks access if store is suspended or trial has expired.
    Superusers bypass all checks (they float above all stores).
    """

    EXEMPT_PATHS = [
        '/login/',
        '/logout/',
        '/register/',
        '/admin/',
        '/superadmin/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.store = None  # always set a default

        if request.user.is_authenticated:
            self._attach_store(request)

        return self.get_response(request)

    def _attach_store(self, request):
        # Superusers float above all stores
        if request.user.is_superuser:
            request.store = None
            return

        # Skip checks on exempt paths
        path = request.path
        if any(path.startswith(p) for p in self.EXEMPT_PATHS):
            return

        store = get_user_store(request.user)

        if store is None:
            # User has no store assigned — send to login
            messages.error(request, "Your account is not linked to any store.")
            request.store = None
            return

        # Check store is active
        if store.status == 'suspended':
            messages.error(request, "Your store has been suspended. Please contact support.")
            request.store = None
            return

        # Check trial hasn't expired
        if store.trial_ends_at and store.trial_ends_at < timezone.now():
            if store.plan == 'starter':  # still on trial plan
                messages.warning(request, "Your trial has expired. Please upgrade your plan.")
                request.store = None
                return

        request.store = store