from django.conf.urls import patterns, url
from reduction_viewer import views


urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^run_list/$', views.run_list, name='run_list'),   
    url(r'^run_queue/$', views.run_queue, name='run_queue'),   
)