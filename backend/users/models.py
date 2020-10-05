from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    push_token = models.CharField(max_length=512, null=True, blank=True)
    push_notification = models.BooleanField(default=False)
    telegram_notification = models.BooleanField(default=False)
    email_notification = models.BooleanField(default=False)
    notification_message = models.CharField(max_length=1024, null=True, blank=True)
