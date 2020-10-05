from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^update/(?P<pk>.*)$', views.update_alert, name='update_alert'),
    url(r'^delete/(?P<pk>.*)$', views.delete_alert, name='delete_alert'),
    url(r'^deleteAllDashboardAlert$', views.delete_all_dashboard_alert, name='delete_all_dashboard_alert'),
    url(r'^create/$', views.create_alert, name='create_alert'),
    url(r'^dashboardAlert$', views.dashboard_alert, name='dashboard_alert'),
    url(r'^(?P<pk>.*)$', views.list_alert, name='alert'),
]
