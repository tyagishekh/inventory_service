from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Reservation, Inventory, InventoryMovement
from django.db import transaction

class Command(BaseCommand):
    help = "Release reservations that have expired"

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Reservation.objects.filter(expires_at__lte=now, released=False)
        count = expired.count()
        self.stdout.write(f"Found {count} expired reservations")
        for r in expired.select_for_update():
            with transaction.atomic():
                try:
                    inv = Inventory.objects.select_for_update().get(sku=r.sku, warehouse=r.warehouse)
                except Inventory.DoesNotExist:
                    # nothing to do, mark released
                    r.released = True
                    r.save()
                    continue
                inv.reserved = max(inv.reserved - r.qty, 0)
                inv.save()
                InventoryMovement.objects.create(inventory=inv, movement_type="RELEASE", qty=r.qty, reference=r.reference)
                r.released = True
                r.save()
                self.stdout.write(f"Released reservation {r.id} sku={r.sku} qty={r.qty}")
        self.stdout.write("Done.")
