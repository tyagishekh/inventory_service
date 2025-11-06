from rest_framework import serializers
from .models import Inventory, InventoryMovement, Reservation

class InventorySerializer(serializers.ModelSerializer):
    #available = serializers.IntegerField(read_only=True, source='available')

    class Meta:
        model = Inventory
        fields = ["id", "product_id", "sku", "warehouse", "on_hand", "reserved", "available", "low_stock_threshold", "updated_at"]

class InventoryMovementSerializer(serializers.ModelSerializer):
    inventory = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = InventoryMovement
        fields = ["id", "inventory", "movement_type", "qty", "reference", "created_at"]

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "sku", "warehouse", "qty", "reference", "created_at", "expires_at", "released", "idempotency_key"]
