from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth import views as authviews

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # default to projdb app
    (r'^$', 'projdb.views.index'),
    # projects
    (r'^projects/', include('projdb.urls')),
    
    # authentication
    (r'^accounts/login/$',              'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^accounts/logout/$',             'django.contrib.auth.views.logout_then_login'),
    (r'^accounts/password_change/$',    'django.contrib.auth.views.password_change'),
    (r'^accounts/password_reset/$',     'django.contrib.auth.views.password_reset'),
    (r'^accounts/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    
    # admin
    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)