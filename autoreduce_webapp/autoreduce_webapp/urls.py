from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^reduction_viewer/', include('reduction_viewer.urls')),
)
