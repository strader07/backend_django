from django.contrib.auth.models import User
from django.db import models


class Alert(models.Model):
    name = models.CharField(max_length=512, null=True, blank=True, verbose_name='Name')
    exchange = models.CharField(max_length=512, null=True, blank=True, verbose_name='Exchange')
    security_type = models.CharField(max_length=512, null=True, blank=True, verbose_name='Security Type')
    base_pair = models.CharField(max_length=512, null=True, blank=True, verbose_name='Base Pair')
    symbols = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Pairs')
    rule = models.TextField(null=True, blank=True, verbose_name='Rule')
    parameters = models.TextField(null=True, blank=True, verbose_name='Parameters')
    is_active = models.BooleanField(default=False, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Updated At')
    owner = models.ForeignKey(User, null=True, blank=True, verbose_name='Created By', on_delete=models.CASCADE, related_name='alert_owner')


class DashBoardAlert(models.Model):
    alert = models.ForeignKey(Alert, null=True, blank=True, on_delete=models.CASCADE)
    pair_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pair Name')
    optional_str = models.CharField(max_length=100, null=True, blank=True, verbose_name='Optional String')
    low_price = models.FloatField(default=0, verbose_name='Low Price')
    high_price = models.FloatField(default=0, verbose_name='High Price')
    created_at = models.DateTimeField(null=True, blank=True, verbose_name='Listed At')
    updated_at = models.DateTimeField(null=True, blank=True, verbose_name='Updated At')


class MinMaxPrice(models.Model):
    alert = models.ForeignKey(Alert, null=True, blank=True, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=50, null=True, blank=True)
    min_price_week = models.FloatField(default=0)
    max_price_week = models.FloatField(default=0)
    min_price_month = models.FloatField(default=0)
    max_price_month = models.FloatField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    current_week = models.DateTimeField(null=True, blank=True)
    current_month = models.DateTimeField(null=True, blank=True)
