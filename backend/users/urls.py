from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^signup/$', views.signup, name='register'),
    url(r'^signin/$', views.signin, name='login'),
    url(r'^getUser/$', views.getUser, name='getUser'),
    url(r'^getUserData/$', views.getUserData, name='getUserData'),
    url(r'^updateUser/$', views.updateUser, name='updateUser')
]
