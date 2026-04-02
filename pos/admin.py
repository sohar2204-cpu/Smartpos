from django.contrib import admin
from .models import *

admin.site.site_header = "Smart Retail POS — Admin"
admin.site.site_title = "SmartPOS"
admin.site.index_title = "Administration Panel"

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'tax_rate', 'created_at']
    search_fields = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'store', 'phone']
    list_filter = ['role', 'store']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store']
    search_fields = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'store']
    search_fields = ['name']

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    readonly_fields = ['product_name', 'unit_price', 'total_price', 'returned_quantity']
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'barcode', 'category', 'price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active', 'store']
    search_fields = ['name', 'barcode']
    list_editable = ['price', 'stock_quantity']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'cashier', 'customer', 'total_amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'store']
    search_fields = ['sale_number']
    readonly_fields = ['sale_number', 'subtotal', 'tax_amount', 'total_amount', 'change_amount']
    inlines = [SaleItemInline]

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['sale', 'sale_item', 'quantity_returned', 'refund_amount', 'processed_by', 'created_at']

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['store', 'currency_symbol', 'updated_at']