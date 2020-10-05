from django.contrib import admin

from alert.models import Alert, DashBoardAlert, MinMaxPrice


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at', 'updated_at')


@admin.register(DashBoardAlert)
class DashBoardAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'alert_id', 'pair_name', 'low_price', 'high_price', 'created_at')


@admin.register(MinMaxPrice)
class MinMaxPriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'min_price_week', 'max_price_week', 'min_price_month', 'max_price_month')
    readonly_fields = ('symbol', 'min_price_week', 'max_price_week', 'min_price_month', 'max_price_month', 'created_at', 'current_week', 'current_month')
