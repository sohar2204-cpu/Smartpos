import hashlib
import secrets
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone


class Store(models.Model):
    PLAN_CHOICES = [
        ('starter',    'Starter'),
        ('pro',        'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('suspended', 'Suspended'),
    ]

    name          = models.CharField(max_length=200)
    address       = models.TextField(blank=True)
    phone         = models.CharField(max_length=20, blank=True)
    email         = models.EmailField(blank=True)
    plan          = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    tax_rate      = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at    = models.DateTimeField(auto_now_add=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subdomain     = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    ]
    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role  = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # FIX SEC-PIN-01: Store a salted SHA-256 hash, never the plain PIN.
    # Format: "sha256$<hex_salt>$<hex_digest>"
    pin_hash = models.CharField(
        max_length=128, blank=True,
        help_text="Salted hash of the 4-digit PIN. Never store raw PINs."
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role in ['admin', 'manager']

    # ── PIN helpers ────────────────────────────────────────────────────────
    def set_pin(self, raw_pin: str):
        """Hash and store a 4-digit PIN."""
        if not raw_pin or not raw_pin.isdigit() or len(raw_pin) != 4:
            raise ValueError("PIN must be exactly 4 digits.")
        salt = secrets.token_hex(16)
        digest = hashlib.sha256(f"{salt}{raw_pin}".encode()).hexdigest()
        self.pin_hash = f"sha256${salt}${digest}"

    def check_pin(self, raw_pin: str) -> bool:
        """Return True if raw_pin matches the stored hash."""
        if not self.pin_hash or not raw_pin:
            return False
        try:
            algo, salt, stored = self.pin_hash.split('$')
        except ValueError:
            return False
        candidate = hashlib.sha256(f"{salt}{raw_pin}".encode()).hexdigest()
        return secrets.compare_digest(candidate, stored)

    def clear_pin(self):
        self.pin_hash = ''


class Supplier(models.Model):
    name         = models.CharField(max_length=200)
    phone        = models.CharField(max_length=20, blank=True)
    email        = models.EmailField(blank=True)
    address      = models.TextField(blank=True)
    store        = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    balance_owed = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Amount owed to supplier"
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name       = models.CharField(max_length=100)
    store      = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    # FIX MODEL-01: Removed duplicate field declarations (barcode & store were defined twice).
    name                = models.CharField(max_length=200)
    barcode             = models.CharField(max_length=100)
    category            = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price               = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity      = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    reorder_quantity    = models.IntegerField(default=0, help_text="Suggested reorder quantity")
    supplier            = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    store               = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    image               = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('barcode', 'store')]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return 'out'
        elif self.is_low_stock:
            return 'low'
        return 'ok'


class Customer(models.Model):
    name           = models.CharField(max_length=200)
    phone          = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    address        = models.TextField(blank=True)
    loyalty_points = models.IntegerField(default=0)
    store          = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_purchases(self):
        return self.sale_set.filter(status='completed').count()

    def total_spent(self):
        from django.db.models import Sum
        result = self.sale_set.filter(status='completed').aggregate(total=Sum('total_amount'))
        return result['total'] or 0


class Sale(models.Model):
    STATUS_CHOICES = [
        ('completed',     'Completed'),
        ('refunded',      'Refunded'),
        ('partial_refund','Partial Refund'),
    ]
    PAYMENT_CHOICES = [
        ('cash',   'Cash'),
        ('card',   'Card'),
        ('online', 'Online'),
    ]
    DISCOUNT_CHOICES = [
        ('none',    'None'),
        ('percent', 'Percentage'),
        ('fixed',   'Fixed Amount'),
    ]

    sale_number          = models.CharField(max_length=20, unique=True)
    cashier              = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer             = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    store                = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    subtotal             = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_type        = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default='none')
    discount_value       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loyalty_points_used  = models.IntegerField(default=0)
    loyalty_points_earned= models.IntegerField(default=0)
    total_amount         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method       = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    amount_received      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes                = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale #{self.sale_number}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            # Generate sale number — no nested transaction.atomic() here.
            # The checkout view already wraps everything in transaction.atomic(),
            # and opening a nested atomic block with select_for_update() inside it
            # causes a lock conflict that rolls back the entire checkout transaction.
            store_prefix = f"S{self.store_id}" if self.store_id else "S0"
            last = (
                Sale.objects
                .filter(store=self.store)
                .order_by('-id')
                .first()
            )
            num = (last.id + 1) if last else 1
            self.sale_number = f"{store_prefix}-INV{num:06d}"
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale            = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product         = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name    = models.CharField(max_length=200)
    product_barcode = models.CharField(max_length=100, blank=True)
    quantity        = models.IntegerField()
    unit_price      = models.DecimalField(max_digits=10, decimal_places=2)
    total_price     = models.DecimalField(max_digits=12, decimal_places=2)
    returned_quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def returnable_quantity(self):
        return self.quantity - self.returned_quantity


class Return(models.Model):
    sale             = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    sale_item        = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    quantity_returned= models.IntegerField()
    refund_amount    = models.DecimalField(max_digits=12, decimal_places=2)
    reason           = models.TextField(blank=True)
    processed_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return for {self.sale.sale_number}"


class StoreSettings(models.Model):
    store                   = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='settings')
    receipt_header          = models.TextField(blank=True)
    receipt_footer          = models.TextField(blank=True, default="Thank you for shopping with us!")
    show_cashier_on_receipt = models.BooleanField(default=True)
    show_customer_on_receipt= models.BooleanField(default=True)
    currency_symbol         = models.CharField(max_length=10, default='Rs')
    currency_code           = models.CharField(max_length=10, default='PKR')
    exchange_rate           = models.DecimalField(
                                max_digits=12, decimal_places=6, default=1.000000,
                                help_text="Rate vs base currency.")
    exchange_rate_api_key   = models.CharField(max_length=200, blank=True, default='')
    logo                    = models.ImageField(upload_to='store/', blank=True, null=True)
    whatsapp_enabled        = models.BooleanField(default=False)
    whatsapp_token          = models.TextField(blank=True)
    whatsapp_phone_id       = models.CharField(max_length=100, blank=True)
    whatsapp_template_name  = models.CharField(max_length=100, blank=True, default="receipt")
    gdrive_enabled          = models.BooleanField(default=False)
    gdrive_credentials_json = models.TextField(blank=True)
    gdrive_token_json       = models.TextField(blank=True)
    gdrive_folder_id        = models.CharField(max_length=200, blank=True)
    gdrive_last_backup_url  = models.TextField(blank=True)
    gdrive_last_backup_at   = models.DateTimeField(null=True, blank=True)
    gdrive_backup_on_sale   = models.BooleanField(default=False)
    gdrive_backup_on_expense= models.BooleanField(default=False)
    fbr_enabled             = models.BooleanField(default=False)
    fbr_sandbox_mode        = models.BooleanField(default=True)
    fbr_token               = models.TextField(blank=True)
    fbr_ntn                 = models.CharField(max_length=20, blank=True)
    fbr_business_name       = models.CharField(max_length=200, blank=True)
    fbr_province            = models.CharField(max_length=50, blank=True, default='Punjab')
    fbr_address             = models.CharField(max_length=300, blank=True)
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return f"Settings for {self.store.name}"


class TaxRule(models.Model):
    TAX_TYPE_CHOICES = [
        ('VAT',       'VAT (Value Added Tax)'),
        ('GST',       'GST (Goods & Services Tax)'),
        ('SALES_TAX', 'Sales Tax'),
        ('EXCISE',    'Excise Duty'),
        ('CUSTOM',    'Custom Tax'),
    ]
    APPLY_CHOICES = [
        ('inclusive', 'Inclusive — tax is included in the price'),
        ('exclusive', 'Exclusive — tax is added on top of price'),
    ]
    APPLY_TO_CHOICES = [
        ('all',      'All Products'),
        ('category', 'Specific Category Only'),
    ]

    store      = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='tax_rules', null=True, blank=True)
    name       = models.CharField(max_length=100)
    tax_type   = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default='SALES_TAX')
    rate       = models.DecimalField(max_digits=6, decimal_places=3)
    tax_mode   = models.CharField(max_length=10, choices=APPLY_CHOICES, default='exclusive')
    apply_to   = models.CharField(max_length=10, choices=APPLY_TO_CHOICES, default='all')
    category   = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}% {self.tax_mode})"


class ExpenseCategory(models.Model):
    name  = models.CharField(max_length=100)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Expense(models.Model):
    store      = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    category   = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title      = models.CharField(max_length=200)
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    date       = models.DateField(default=timezone.now)
    notes      = models.TextField(blank=True)
    added_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — Rs {self.amount}"


class SupplierPayment(models.Model):
    supplier       = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[('cash', 'Cash'), ('bank', 'Bank Transfer'), ('cheque', 'Cheque')],
        default='cash'
    )
    reference  = models.CharField(max_length=100, blank=True)
    notes      = models.TextField(blank=True)
    paid_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment to {self.supplier.name} — Rs {self.amount}"


class StockPurchase(models.Model):
    supplier     = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    store        = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes        = models.TextField(blank=True)
    added_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"Purchase from {self.supplier.name} on {self.created_at.date()}"


class StockPurchaseItem(models.Model):
    purchase     = models.ForeignKey(StockPurchase, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    quantity     = models.IntegerField()
    unit_cost    = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost   = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class Shift(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed')]

    cashier           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shifts')
    store             = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    opening_cash      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_cash      = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_cash     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_difference   = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_sales       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions= models.IntegerField(default=0)
    notes             = models.TextField(blank=True)
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    opened_at         = models.DateTimeField(auto_now_add=True)
    closed_at         = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shift — {self.cashier} — {self.opened_at.date()}"


class BackupLog(models.Model):
    store      = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    filename   = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class FBRInvoiceLog(models.Model):
    STATUS_CHOICES = [
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('pending',  'Pending'),
        ('disabled', 'FBR Disabled'),
    ]
    sale           = models.OneToOneField('Sale', on_delete=models.CASCADE, related_name='fbr_log')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fbr_invoice_no = models.CharField(max_length=50, blank=True)
    qr_code_data   = models.TextField(blank=True)
    request_json   = models.TextField(blank=True)
    response_json  = models.TextField(blank=True)
    error_message  = models.TextField(blank=True)
    sandbox_mode   = models.BooleanField(default=True)
    submitted_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"FBR Log — Sale {self.sale.sale_number} — {self.status}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login',           'User Login'),
        ('logout',          'User Logout'),
        ('login_failed',    'Login Failed'),         # FIX: added for tracking failures
        ('pin_login',       'PIN Login'),            # FIX: track PIN logins separately
        ('pin_failed',      'PIN Login Failed'),
        ('sale_complete',   'Sale Completed'),
        ('sale_void',       'Sale Voided / Return'),
        ('product_add',     'Product Added'),
        ('product_edit',    'Product Edited'),
        ('product_delete',  'Product Deleted'),
        ('price_change',    'Price Changed'),
        ('stock_purchase',  'Stock Purchase'),
        ('expense_add',     'Expense Added'),
        ('expense_delete',  'Expense Deleted'),
        ('shift_open',      'Shift Opened'),
        ('shift_close',     'Shift Closed'),
        ('user_add',        'User Added'),
        ('user_edit',       'User Edited'),
        ('backup',          'Backup Created'),
        ('restore',         'Backup Restored'),
        ('settings_change', 'Settings Changed'),
        ('other',           'Other'),
    ]

    action     = models.CharField(max_length=30, choices=ACTION_CHOICES)
    detail     = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
    store      = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} — {self.action} — {self.timestamp.strftime('%Y-%m-%d %H:%M')}"