
from django.core.management.base import BaseCommand
from django.db.models import F
from pos.models import Store, Product
from pos.saas_views import send_low_stock_alert


class Command(BaseCommand):
    help = 'Send low stock alert emails to store admins'

    def handle(self, *args, **options):
        stores = Store.objects.all()
        total_alerts = 0

        for store in stores:
            low = Product.objects.filter(
                store=store,
                is_active=True,
                stock_quantity__lte=F('low_stock_threshold'),
            ).order_by('stock_quantity')

            if low.exists():
                send_low_stock_alert(store, low)
                self.stdout.write(
                    f'  Alert sent for {store.name} — {low.count()} product(s)'
                )
                total_alerts += low.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {total_alerts} low-stock alerts sent across {stores.count()} stores.'
            )
        )
