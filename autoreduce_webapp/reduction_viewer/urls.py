from django.conf.urls import patterns, url
from reduction_viewer import views


urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': 'index'})
    url(r'^run_queue/$', views.run_queue, name='run_queue'),   
)