from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from .utils import get_user_store
from django.shortcuts import redirect
from django.urls import reverse

class RestrictSuperuserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # ONLY force Superadmins to the Admin Panel
            if request.user.is_superuser:
                if not request.path.startswith('/admin/') and request.path != reverse('logout'):
                    return redirect('/admin/')
            
            # DO NOT add an 'else' redirect for regular users here. 
            # Let them go wherever the LOGIN_REDIRECT_URL tells them.

        return self.get_response(request)

class StoreScopeMiddleware:
    """
    Middleware to scope every request to a specific Store.
    - Attaches request.store to the request object.
    - Enforces suspension and trial expiration rules.
    - Exempts administrative and auth paths.
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
        # 1. Default initialization
        request.store = None

        # 2. Bypass for unauthenticated users or Superadmins
        # Superadmins "float" above stores and resolve context in specific views
        if not request.user.is_authenticated or request.user.is_superuser:
            return self.get_response(request)

        # 3. Check if current path is exempt from store-scoping
        path = request.path
        is_exempt = any(path.startswith(p) for p in self.EXEMPT_PATHS)
        
        if is_exempt:
            return self.get_response(request)

        # 4. Resolve the Store
        store = get_user_store(request.user)

        # 5. Validation Logic (Fail-Fast)
        if not store:
            messages.error(request, "Your account is not linked to any store.")
            return redirect('login')

        if store.status == 'suspended':
            # Use a dedicated error template for suspended accounts
            return render(request, 'errors/suspended.html', {'store': store}, status=403)

        # 6. Trial Expiration Check
        if store.trial_ends_at and store.trial_ends_at < timezone.now():
            # If they are still on the starter/trial plan but time is up
            if store.plan == 'starter':
                messages.warning(request, "Your trial has expired. Please upgrade your plan to continue.")
                # You can either redirect to a pricing page or allow restricted access
                # For POS systems, we usually block access to the checkout:
                return render(request, 'errors/trial_expired.html', {'store': store})

        # 7. Success: Attach store and proceed
        request.store = store
        return self.get_response(request)