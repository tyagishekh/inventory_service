from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Inventory, InventoryMovement, Reservation
from rest_framework.exceptions import ValidationError

def _get_inventory_for_update(sku, warehouse):
    try:
        return Inventory.objects.select_for_update().get(sku=sku, warehouse=warehouse)
    except Inventory.DoesNotExist:
        raise ValidationError(f"No inventory row for sku={sku} warehouse={warehouse}")

@transaction.atomic
def reserve(sku, warehouse, qty, reference=None, idempotency_key=None, ttl_seconds=None):
    ttl_seconds = ttl_seconds or 900
    # Idempotency: check existing reservation for same idempotency_key & reference
    if idempotency_key:
        existing = Reservation.objects.filter(idempotency_key=idempotency_key, reference=reference, released=False).first()
        if existing:
            return existing  # already reserved

    inv = _get_inventory_for_update(sku, warehouse)

    if inv.available() < qty:
        raise ValidationError({"detail": "Insufficient stock", "available": inv.available()})

    inv.reserved = inv.reserved + qty
    inv.save()

    expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
    r = Reservation.objects.create(sku=sku, warehouse=warehouse, qty=qty, reference=reference, expires_at=expires_at, idempotency_key=idempotency_key)
    InventoryMovement.objects.create(inventory=inv, movement_type="RESERVE", qty=qty, reference=reference)
    return r

@transaction.atomic
def release(reservation_id=None, sku=None, warehouse=None, qty=None, reference=None, idempotency_key=None):
    """
    Release by reservation_id (preferred) or by sku/warehouse/qty/reference + idempotency.
    """
    # If reservation_id provided, use it
    if reservation_id:
        try:
            r = Reservation.objects.select_for_update().get(id=reservation_id)
        except Reservation.DoesNotExist:
            raise ValidationError("Reservation not found")
        if r.released:
            return r
        inv = Inventory.objects.select_for_update().get(sku=r.sku, warehouse=r.warehouse)
        inv.reserved = max(inv.reserved - r.qty, 0)
        inv.save()
        InventoryMovement.objects.create(inventory=inv, movement_type="RELEASE", qty=r.qty, reference=r.reference)
        r.released = True
        r.save()
        return r

    # else, by idempotency_key
    if idempotency_key:
        existing = Reservation.objects.filter(idempotency_key=idempotency_key, released=True).first()
        if existing:
            return existing

    # fallback: by sku/warehouse
    if not (sku and warehouse and qty is not None):
        raise ValidationError("Provide reservation_id or (sku, warehouse, qty)")

    inv = _get_inventory_for_update(sku, warehouse)
    inv.reserved = max(inv.reserved - qty, 0)
    inv.save()
    InventoryMovement.objects.create(inventory=inv, movement_type="RELEASE", qty=qty, reference=reference)
    # create a synthetic released reservation record for audit
    r = Reservation.objects.create(sku=sku, warehouse=warehouse, qty=qty, reference=reference, expires_at=timezone.now(), released=True, idempotency_key=idempotency_key)
    return r

@transaction.atomic
def ship(sku, warehouse, qty, reference=None, idempotency_key=None):
    inv = _get_inventory_for_update(sku, warehouse)
    if inv.reserved < qty:
        raise ValidationError(f"Cannot ship {qty} — only {inv.reserved} reserved")
    inv.reserved = inv.reserved - qty
    inv.on_hand = inv.on_hand - qty
    inv.save()
    InventoryMovement.objects.create(inventory=inv, movement_type="SHIP", qty=qty, reference=reference)
    return inv
