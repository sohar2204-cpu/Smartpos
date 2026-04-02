from django.core.exceptions import PermissionDenied
from .models import AuditLog

def get_user_store(user):
    """Returns the Store for a given user. None for superusers."""
    if user.is_superuser:
        return None
    try:
        return user.profile.store
    except Exception:
        return None


def store_queryset(model, request):
    """
    Returns a queryset of model filtered to request.store.
    Use this as the base for every query in your views.
    
    Usage:
        products = store_queryset(Product, request)
        sales = store_queryset(Sale, request).filter(status='completed')
    """
    if request.user.is_superuser:
        return model.objects.all()
    if not request.store:
        return model.objects.none()
    return model.objects.filter(store=request.store)


def log_action(request, action, detail=''):
    """
    Logs user actions with store scoping.
    """
    try:
        user = request.user if request.user.is_authenticated else None
        store = getattr(request, 'store', None)

        # Get IP address
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')

        AuditLog.objects.create(
            user=user,
            store=store,
            action=action,
            detail=detail,
            ip_address=ip
        )
    except Exception:
        # Never crash app due to logging
        pass