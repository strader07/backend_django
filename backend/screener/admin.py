from django.contrib import admin

from screener.models import Screener, DashBoardScreener


@admin.register(Screener)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at', 'updated_at')


@admin.register(DashBoardScreener)
class DashBoardScreener(admin.ModelAdmin):
    list_display = ('id', 'screener_id', 'pair_name')
