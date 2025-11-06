from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet, MovementViewSet, ReservationViewSet

router = DefaultRouter()
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'movements', MovementViewSet, basename='movements')
router.register(r'reservations', ReservationViewSet, basename='reservations')

urlpatterns = router.urls
