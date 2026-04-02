import json
import threading
from datetime import timedelta
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from .models import Store, UserProfile, StoreSettings, Sale, Product, Customer


# ══════════════════════════════════════════════════════════════════════════════
# TENANT SELF-SIGNUP
# ══════════════════════════════════════════════════════════════════════════════

def register_view(request):
    """
    Public self-signup page.
    GET  → render register.html
    POST → validate → create Store + User + UserProfile + StoreSettings → JSON
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # ── Collect ───────────────────────────────────────────────────────
        first_name      = request.POST.get('first_name',      '').strip()
        last_name       = request.POST.get('last_name',       '').strip()
        username        = request.POST.get('username',        '').strip()
        email           = request.POST.get('email',           '').strip()
        password        = request.POST.get('password',        '').strip()
        store_name      = request.POST.get('store_name',      '').strip()
        phone           = request.POST.get('phone',           '').strip()
        address         = request.POST.get('address',         '').strip()
        business_type   = request.POST.get('business_type',   'retail')
        currency_symbol = request.POST.get('currency_symbol', 'Rs')
        plan            = request.POST.get('plan',            'starter')

        # ── Validate ──────────────────────────────────────────────────────
        if not first_name:
            return JsonResponse({'success': False, 'error': 'First name is required.'})
        if not username or ' ' in username:
            return JsonResponse({'success': False, 'error': 'Username is required and cannot contain spaces.'})
        if not email or '@' not in email:
            return JsonResponse({'success': False, 'error': 'A valid email address is required.'})
        if len(password) < 8:
            return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'})
        if not store_name:
            return JsonResponse({'success': False, 'error': 'Store name is required.'})
        if plan not in ('starter', 'pro', 'enterprise'):
            plan = 'starter'

        # ── Uniqueness checks ─────────────────────────────────────────────
        if User.objects.filter(username__iexact=username).exists():
            return JsonResponse({'success': False,
                                 'error': f'Username "{username}" is already taken. Please choose another.'})
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({'success': False,
                                 'error': 'An account with that email already exists.'})
        if Store.objects.filter(name__iexact=store_name).exists():
            return JsonResponse({'success': False,
                                 'error': f'A store named "{store_name}" already exists.'})

        try:
            # ── Create Store ──────────────────────────────────────────────
            store = Store.objects.create(
                name=store_name,
                phone=phone,
                address=address,
                email=email,
                plan=plan,
                status='active',
                subdomain=slugify(store_name)
) 
            store.trial_ends_at = timezone.now() + timedelta(days=7)
            store.save()

            # ── Create StoreSettings with currency ────────────────────────
            StoreSettings.objects.create(
                store=store,
                currency_symbol=currency_symbol,
                receipt_footer=f'Thank you for shopping at {store_name}!',
            )

            # ── Create User ───────────────────────────────────────────────
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                
            )

            # ── Create UserProfile — admin of their own store ─────────────
            UserProfile.objects.create(
                user=user,
                role='admin',
                store=store,
                phone=phone,
            )

            return JsonResponse({
              'success': True,
              'redirect_url': '/dashboard/'
        })
            login(request, user)
        except Exception as e:
            return JsonResponse({'success': False,
                                 'error': f'Registration failed: {str(e)}'})

    # GET
    return render(request, 'pos/register.html')


# ══════════════════════════════════════════════════════════════════════════════
# SUPERADMIN HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def is_superadmin(user):
    try:
        return user.is_staff or (
            user.profile.role == 'admin' and not user.profile.store
        )
    except Exception:
        return user.is_staff


def superadmin_required(view_fn):
    from functools import wraps
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not is_superadmin(request.user):
            messages.error(request, 'Access denied. Platform admins only.')
            return redirect('dashboard')
        return view_fn(request, *args, **kwargs)
    return wrapper


def _enrich_store(store):
    from datetime import date, timedelta
    today      = timezone.now().date()
    thirty_ago = today - timedelta(days=30)
    sales_qs   = Sale.objects.filter(
        store=store, status='completed', created_at__date__gte=thirty_ago
    )
    revenue_30d  = sales_qs.aggregate(t=Sum('total_amount'))['t'] or 0
    user_count   = UserProfile.objects.filter(store=store).count()
    owner        = UserProfile.objects.filter(store=store, role='admin').first()
    return {
        'id':            store.id,
        'name':          store.name,
        'owner_username': owner.user.username if owner else '—',
        'plan':          getattr(store, 'plan',   'starter'),
        'status':        getattr(store, 'status', 'active'),
        'user_count':    user_count,
        'sales_30d':     sales_qs.count(),
        'revenue_30d':   revenue_30d,
        'created_at':    store.created_at,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SUPERADMIN VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@superadmin_required
def superadmin_dashboard(request):
    from datetime import date, timedelta
    today    = timezone.now().date()
    week_ago = today - timedelta(days=7)

    all_stores  = Store.objects.all().order_by('-created_at')
    today_sales = Sale.objects.filter(status='completed', created_at__date=today)
    stores      = [_enrich_store(s) for s in all_stores]

    return render(request, 'pos/superadmin_dashboard.html', {
        'total_stores':           all_stores.count(),
        'new_stores_week':        Store.objects.filter(created_at__date__gte=week_ago).count(),
        'total_users':            User.objects.count(),
        'total_sales_today':      today_sales.count(),
        'platform_revenue_today': today_sales.aggregate(t=Sum('total_amount'))['t'] or 0,
        'stores':                 stores,
        'recent_signups':         stores[:5],
        'suspended_stores':       [s for s in stores if s['status'] == 'suspended'],
    })


@login_required
@superadmin_required
def superadmin_suspend_store(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    if request.method == 'POST':
        ids = UserProfile.objects.filter(store=store).values_list('user_id', flat=True)
        User.objects.filter(id__in=ids).update(is_active=False)
        store.status = 'suspended'
        store.save(update_fields=['status'])
        messages.success(request, f'Store "{store.name}" suspended.')
    return redirect('superadmin_dashboard')


@login_required
@superadmin_required
def superadmin_activate_store(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    ids   = UserProfile.objects.filter(store=store).values_list('user_id', flat=True)
    User.objects.filter(id__in=ids).update(is_active=True)
    store.status = 'active'
    store.save(update_fields=['status'])
    messages.success(request, f'Store "{store.name}" activated.')
    return redirect('superadmin_dashboard')


@login_required
@superadmin_required
def superadmin_login_as(request, store_id):
    from django.conf import settings as django_settings
    if not django_settings.DEBUG:
        messages.error(request, 'Impersonation is disabled in production.')
        return redirect('superadmin_dashboard')
    store   = get_object_or_404(Store, id=store_id)
    profile = UserProfile.objects.filter(store=store, role='admin').first()
    if not profile:
        messages.error(request, 'No admin user for this store.')
        return redirect('superadmin_dashboard')
    from django.contrib.auth import login
    login(request, profile.user,
          backend='django.contrib.auth.backends.ModelBackend')
    messages.info(request, f'Now logged in as {profile.user.username} ({store.name})')
    return redirect('dashboard')


@login_required
@superadmin_required
def superadmin_add_store(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        username   = request.POST.get('username',   '').strip()
        password   = request.POST.get('password',   '').strip()
        email      = request.POST.get('email',      '').strip()

        if not all([store_name, username, password]):
            messages.error(request, 'Store name, username, and password are required.')
            return redirect('superadmin_add_store')
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('superadmin_add_store')

        store = Store.objects.create(name=store_name, email=email,
                                     plan='starter', status='active')
        user  = User.objects.create_user(username=username,
                                         password=password, email=email)
        UserProfile.objects.create(user=user, role='admin', store=store)
        StoreSettings.objects.get_or_create(store=store)
        messages.success(request,
            f'Store "{store_name}" and admin "{username}" created.')
        return redirect('superadmin_dashboard')

    return render(request, 'pos/superadmin_add_store.html')
