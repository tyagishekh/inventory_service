from django.db import models
from django.utils import timezone
import uuid

class Inventory(models.Model):
    """
    Per SKU per warehouse inventory.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(null=True, blank=True)  # logical product_id from catalog (no DB FK)
    sku = models.CharField(max_length=128)
    warehouse = models.CharField(max_length=64)
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("sku", "warehouse")
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["warehouse"]),
        ]

    def available(self):
        return self.on_hand - self.reserved

    def __str__(self):
        return f"{self.sku}@{self.warehouse}"

class Reservation(models.Model):
    """
    Tracks a reservation made against inventory for an order or hold.
    Idempotency is keyed either by idempotency_key or reservation_uuid.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=128)
    warehouse = models.CharField(max_length=64)
    qty = models.IntegerField()
    reference = models.CharField(max_length=255, null=True, blank=True)  # e.g., order_id
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    released = models.BooleanField(default=False)
    idempotency_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

class InventoryMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("IN", "IN"),
        ("OUT", "OUT"),
        ("RESERVE", "RESERVE"),
        ("RELEASE", "RELEASE"),
        ("SHIP", "SHIP"),
        ("ADJUST", "ADJUST"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=16, choices=MOVEMENT_CHOICES)
    qty = models.IntegerField()
    reference = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
