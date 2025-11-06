from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'warehouse', 'on_hand', 'reserved', 'updated_at')
    search_fields = ('product_id', 'warehouse')
