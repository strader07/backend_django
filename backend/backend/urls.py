from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('screener/', include('screener.urls')),
    path('alert/', include('alert.urls')),
]
