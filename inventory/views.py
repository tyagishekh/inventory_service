from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Inventory, InventoryMovement, Reservation
from .serializers import InventorySerializer, InventoryMovementSerializer, ReservationSerializer
from . import services
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.db import transaction

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().order_by("sku")
    serializer_class = InventorySerializer
    lookup_field = "id"

    @action(detail=False, methods=["get"])
    def by_sku(self, request):
        sku = request.query_params.get("sku")
        if not sku:
            return Response({"detail": "sku required"}, status=400)
        qs = Inventory.objects.filter(sku=sku)
        return Response(InventorySerializer(qs, many=True).data)

    @action(detail=False, methods=["post"])
    def reserve(self, request):
        # Accept Idempotency-Key header
        idempotency_key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        sku = request.data.get("sku")
        warehouse = request.data.get("warehouse")
        qty = int(request.data.get("quantity", 0))
        reference = request.data.get("reference")
        ttl = int(request.data.get("ttl_seconds", settings.RESERVATION_TTL_SECONDS))
        if not sku or not warehouse or qty <= 0:
            raise ValidationError("sku, warehouse, and positive quantity required")
        try:
            r = services.reserve(sku=sku, warehouse=warehouse, qty=qty, reference=reference, idempotency_key=idempotency_key, ttl_seconds=ttl)
        except ValidationError as e:
            return Response({"detail": str(e.detail if hasattr(e,'detail') else e)}, status=409)
        return Response(ReservationSerializer(r).data, status=200)

    @action(detail=False, methods=["post"])
    def release(self, request):
        idempotency_key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        reservation_id = request.data.get("reservation_id")
        sku = request.data.get("sku")
        warehouse = request.data.get("warehouse")
        qty = request.data.get("quantity")
        reference = request.data.get("reference")
        try:
            r = services.release(reservation_id=reservation_id, sku=sku, warehouse=warehouse, qty=qty, reference=reference, idempotency_key=idempotency_key)
        except ValidationError as e:
            return Response({"detail": str(e.detail if hasattr(e,'detail') else e)}, status=400)
        return Response(ReservationSerializer(r).data, status=200)

    @action(detail=False, methods=["post"])
    def ship(self, request):
        idempotency_key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        sku = request.data.get("sku")
        warehouse = request.data.get("warehouse")
        qty = int(request.data.get("quantity", 0))
        reference = request.data.get("reference")
        if not sku or not warehouse or qty <= 0:
            raise ValidationError("sku, warehouse, and positive quantity required")
        try:
            inv = services.ship(sku=sku, warehouse=warehouse, qty=qty, reference=reference, idempotency_key=idempotency_key)
        except ValidationError as e:
            return Response({"detail": str(e.detail if hasattr(e,'detail') else e)}, status=409)
        return Response(InventorySerializer(inv).data, status=200)

class MovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryMovement.objects.all().order_by("-created_at")
    serializer_class = InventoryMovementSerializer

class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reservation.objects.all().order_by("-created_at")
    serializer_class = ReservationSerializer
