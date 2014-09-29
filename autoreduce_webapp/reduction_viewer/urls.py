from django.conf.urls import patterns, url
from reduction_viewer import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'))