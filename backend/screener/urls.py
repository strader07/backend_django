from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^update/(?P<pk>.*)$', views.update_screener, name='update_screener'),
    url(r'^delete/(?P<pk>.*)$', views.delete_screener, name='delete'),
    url(r'^create/$', views.create_screener, name='create_screener'),
    url(r'^dashboardScreener$', views.dashboard_screener, name='dashboard_screener'),
    url(r'^(?P<pk>.*)$', views.list_screener, name='screener'),
]
