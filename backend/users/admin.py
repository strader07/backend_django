from django.contrib import admin

from users.models import Profile


@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ('id', 'owner')
    readonly_fields = ('push_token', 'owner')
