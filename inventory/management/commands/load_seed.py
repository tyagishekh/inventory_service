import csv
from django.core.management.base import BaseCommand
from inventory.models import Inventory
from django.utils import timezone
from pathlib import Path

class Command(BaseCommand):
    help = "Load inventory seed CSV: sku,warehouse,on_hand,reserved,low_stock_threshold,product_id (optional)"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        path = options['path']
        p = Path(path)
        if not p.exists():
            self.stdout.write(self.style.ERROR(f"{path} not found"))
            return
        with open(p) as f:
            reader = csv.DictReader(f)
            for row in reader:
                inv, created = Inventory.objects.update_or_create(
                    sku=row['sku'],
                    warehouse=row['warehouse'],
                    defaults={
                        "on_hand": int(row.get('on_hand', 0)),
                        "reserved": int(row.get('reserved', 0)),
                        "low_stock_threshold": int(row.get('low_stock_threshold', 0)) if row.get('low_stock_threshold') else 0,
                    }
                )
                self.stdout.write(f"Loaded {inv.sku}@{inv.warehouse} on_hand={inv.on_hand}")
