from django.contrib.auth.models import User
from django.db import models


class Screener(models.Model):
    name = models.CharField(max_length=512, null=True, blank=True, verbose_name='Name')
    exchange = models.CharField(max_length=512, null=True, blank=True, verbose_name='Exchange')
    security_type = models.CharField(max_length=512, null=True, blank=True, verbose_name='Security Type')
    base_pair = models.CharField(max_length=512, null=True, blank=True, verbose_name='Base Pair')
    rule = models.TextField(null=True, blank=True, verbose_name='Rule')
    parameters = models.TextField(null=True, blank=True, verbose_name='Parameters')
    is_active = models.BooleanField(default=False, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Updated At')
    owner = models.ForeignKey(User, null=True, blank=True, verbose_name='Created By', on_delete=models.CASCADE, related_name='screen_owner')


class DashBoardScreener(models.Model):
    screener = models.ForeignKey(Screener, null=True, blank=True, on_delete=models.CASCADE)
    pair_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pair Name')
    initial_price = models.FloatField(default=0, verbose_name='Initial Price')
    current_price = models.FloatField(default=0, verbose_name='Current Price')
    created_at = models.DateTimeField(null=True, blank=True, verbose_name='Listed At')
    updated_at = models.DateTimeField(null=True, blank=True, verbose_name='Updated At')
