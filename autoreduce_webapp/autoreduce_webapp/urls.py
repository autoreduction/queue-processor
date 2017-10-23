from django.conf.urls import include, url
from django.contrib import admin
from reduction_viewer import views as reduction_viewer_views
from reduction_variables import views as reduction_variables_views

handler400 = 'autoreduce_webapp.views.handler400'
handler403 = 'autoreduce_webapp.views.handler403'
handler404 = 'autoreduce_webapp.views.handler404'
handler500 = 'autoreduce_webapp.views.handler500'

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', reduction_viewer_views.index, name='index'),
    url(r'^logout/$', reduction_viewer_views.logout, name='logout'),

    url(r'^runs/$', reduction_viewer_views.run_list, name='run_list'),   
    url(r'^runs/queue/$', reduction_viewer_views.run_queue, name='run_queue'), 
    url(r'^runs/failed/$', reduction_viewer_views.fail_queue, name='fail_queue'),
    url(r'^runs/list/(?P<reference_number>[0-9]+)/$', reduction_viewer_views.load_runs, name='load_runs'),
    url(r'^runs/list/(?P<instrument_name>\w+)/$', reduction_viewer_views.load_runs, name='load_runs'),
    url(r'^runs/(?P<run_number>[0-9]+)(?:/(?P<run_version>[0-9]+))?/$', reduction_viewer_views.run_summary, name='run_summary'),
    url(r'^runs/(?P<instrument>\w+)/confirmation/$', reduction_variables_views.run_confirmation, name='run_confirmation'),

    url(r'^instrument/(?P<instrument>\w+)/$', reduction_viewer_views.instrument_summary, name='instrument_summary'),
    url(r'^instrument/(?P<instrument>\w+)/pause$', reduction_viewer_views.instrument_pause, name='instrument_pause'),
    url(r'^instrument/(?P<instrument>\w+)/submit_runs/$', reduction_variables_views.submit_runs, name='instrument_submit_runs'),
    url(r'^instrument/(?P<instrument>\w+)/variables/$', reduction_variables_views.instrument_variables, name='instrument_variables'),
    url(r'^instrument/(?P<instrument>\w+)/variables(?:/(?P<start>[0-9]+))?(?:/(?P<end>[0-9]+))?/$', reduction_variables_views.instrument_variables, name='instrument_variables'),
    url(r'^instrument/(?P<instrument>\w+)/variables(?:/(?P<start>[0-9]+))?(?:/(?P<end>[0-9]+))?/delete$', reduction_variables_views.delete_instrument_variables, name='delete_instrument_variables'),
    url(r'^instrument/(?P<instrument>\w+)/variables/experiment/(?P<experiment_reference>[0-9]+)/$', reduction_variables_views.instrument_variables, name='instrument_variables_by_experiment'),
    url(r'^instrument/(?P<instrument>\w+)/variables/experiment/(?P<experiment_reference>[0-9]+)/delete$', reduction_variables_views.delete_instrument_variables, name='delete_instrument_variables_by_experiment'),

    url(r'^instrument/(?P<instrument>\w+)/default_variables/$', reduction_variables_views.current_default_variables, name='current_default_variables'),

    url(r'^experiment/(?P<reference_number>[0-9]+)/$', reduction_viewer_views.experiment_summary, name='experiment_summary'),       

    url(r'^script/(?P<instrument>\w+)(?:/(?P<run_number>[0-9]+))?/$', reduction_variables_views.preview_script, name='preview_script'),
    url(r'^script/(?P<instrument>\w+)/experiment(?:/(?P<experiment_reference>[0-9]+))?/$', reduction_variables_views.preview_script, name='preview_script_by_experiment'),

    url(r'^help/$', reduction_viewer_views.help, name='help')
]
