from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def store_required(view_func):
    """
    Ensures the user is logged in AND has an active store attached.
    Use this on every POS view instead of just @login_required.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            # Superadmin can access everything
            return view_func(request, *args, **kwargs)

        if not request.store:
            messages.error(request, "No active store found for your account.")
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    """
    Restricts a view to users with specific roles.
    Usage: @role_required('admin', 'manager')
    Always combine with @store_required.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            try:
                user_role = request.user.profile.role
            except Exception:
                messages.error(request, "Profile not found.")
                return redirect('login')

            if user_role not in roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def superadmin_required(view_func):
    """
    Restricts a view to Django superusers only (platform admins).
    Use this on all /superadmin/ views.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Access denied.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper