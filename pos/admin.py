from django.contrib import admin
from django.shortcuts import render
from django.utils import timezone          # Added
from datetime import timedelta             # Added
from django.db.models import Sum           # Added
from .models import *

# 1. Custom Admin Site to handle Privacy and the Dashboard
class SmartPOSAdminSite(admin.AdminSite):
    site_header = "Smart Retail POS — Admin"
    site_title = "SmartPOS"
    index_title = "Administration Panel"

    # This redirects the Superadmin to your custom dashboard
    def index(self, request, extra_context=None):
        if request.user.is_superuser:
            today = timezone.now().date()
            seven_days_ago = today - timedelta(days=7)
            thirty_days_ago = today - timedelta(days=30)

            # --- Calculate Stats for Dashboard ---
            stores_queryset = Store.objects.all()
            
            # KPI Data
            total_stores = stores_queryset.count()
            new_stores_week = stores_queryset.filter(created_at__gte=seven_days_ago).count()
            total_users = UserProfile.objects.count()
            
            # Combined Sales/Revenue (All Stores)
            sales_today = Sale.objects.filter(created_at__date=today)
            total_sales_today = sales_today.count()
            platform_revenue_today = sales_today.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            # --- Prepare Store Table Data ---
            # We annotate each store with its 30-day stats
            stores_list = []
            for s in stores_queryset:
                # Note: Adjust field names (like 'status' or 'plan') to match your actual Store model
                s_sales = Sale.objects.filter(store=s, created_at__gte=thirty_days_ago)
                
                stores_list.append({
                    'id': s.id,
                    'name': s.name,
                    'owner_username': s.email, # Or s.owner.username if linked to User
                    'status': 'active', # Replace with s.status if field exists
                    'plan': 'pro',      # Replace with s.plan if field exists
                    'user_count': s.userprofile_set.count(),
                    'sales_30d': s_sales.count(),
                    'revenue_30d': s_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
                    'created_at': s.created_at,
                })

            context = {
                **self.each_context(request),
                'total_stores': total_stores,
                'new_stores_week': new_stores_week,
                'total_users': total_users,
                'total_sales_today': total_sales_today,
                'platform_revenue_today': platform_revenue_today,
                'stores': stores_list,
                'recent_signups': stores_list[:5], # Last 5
                'suspended_stores': [s for s in stores_list if s['status'] == 'suspended'],
            }
            return render(request, 'pos/superadmin_dashboard.html', context)
        
        return super().index(request, extra_context)

    # Privacy Filter: Hide "Store Content" models from the Superadmin Sidebar
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if request.user.is_superuser:
            # List of models the Superadmin is ALLOWED to see
            allowed_models = ['Store', 'UserProfile', 'StoreSettings']
            for app in app_list:
                app['models'] = [m for m in app['models'] if m['object_name'] in allowed_models]
        return app_list

# Initialize the custom site
admin_site = SmartPOSAdminSite(name='smartpos_admin')

# 2. Register Models to the CUSTOM admin_site (not the default admin.site)
@admin.register(Store, site=admin_site)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'tax_rate', 'created_at']
    search_fields = ['name']

@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'store', 'phone']
    list_filter = ['role', 'store']

@admin.register(StoreSettings, site=admin_site)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['store', 'currency_symbol', 'updated_at']

# These models remain registered but will be HIDDEN from the Superadmin sidebar
@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store']

@admin.register(Supplier, site=admin_site)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'store']

@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'barcode', 'category', 'price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active', 'store']

@admin.register(Customer, site=admin_site)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']

@admin.register(Sale, site=admin_site)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'cashier', 'total_amount', 'status', 'created_at']
    readonly_fields = ['sale_number', 'total_amount']

@admin.register(Return, site=admin_site)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['sale', 'refund_amount', 'created_at']