from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# test comment
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r"^article/new/$", "app.views.newArticle"),
    url(r"^article/upload/$", "app.views.fileUpload", name="fileUpload"),
    url(r"^article/upload/recent/$", "app.views.recentFiles", name="recentFiles"),
    url(r"^article/(?P<jslug>[\-\d\w]+)/$", "app.views.article"),
    url(r"^category/(?P<jslug>[\-\d\w]+)/$", "app.views.category"),
    url(r"^article/(?P<jslug>[\-\d\w]+)/edit/$", "app.views.articleEditor"),
    url(r"^staff/$", "app.views.staffHome"),
    url(r"^staff/profile/$", "app.views.profilePage"),
    url(r"^login/$", 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
