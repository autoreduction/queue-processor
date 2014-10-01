from django.conf.urls import include, url, patterns
from django.contrib import admin
from reduction_viewer import views as reduction_viewer_views
from reduction_variables import views as reduction_variables_views

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', reduction_viewer_views.index, name='index'),
    url(r'^logout/$', reduction_viewer_views.logout, name='logout'),

    url(r'^runs/$', reduction_viewer_views.run_list, name='run_list'),   
    url(r'^runs/queue/$', reduction_viewer_views.run_queue, name='run_queue'), 
    url(r'^runs/(?P<run_number>[0-9]+)/$', reduction_viewer_views.run_summary, name='run_summary'),  
    url(r'^runs/(?P<run_number>[0-9]+)/confirmation/$', reduction_variables_views.run_confirmation, name='run_confirmation'),  

    url(r'^instrument/(?P<instrument>\w+)/$', reduction_viewer_views.instrument_summary, name='instrument_summary'),       
    url(r'^instrument/(?P<instrument>\w+)/variables/$', reduction_variables_views.instrument_variables, name='instrument_variables'),       

    url(r'^experiment/(?P<reference_number>[0-9]+)/$', reduction_viewer_views.experiment_summary, name='experiment_summary'),       
)
