from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# test comment
from django.contrib import admin
from main.settings import ENVIRONMENT, MEDIA_ROOT

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r"^category/(?P<jslug>[\-\d\w]+)/$", "app.views.category"),
    url(r"^article/(?P<article_id>[\-\d\w]+)/$", "app.views.article", {'type':'articleView'}),
    url(r"^author/(?P<jslug>[\-\d\w]+)/$", "app.views.authorPage"),
    url(r"^staff/$", "app.views.staffHome"),
    url(r"^staff/profile/$", "app.views.profilePage"),
    url(r"^staff/image/(?P<image_id>\d+)/", "app.views.imageEditor"),
    url(r"^staff/image/upload/$","app.views.imageUpload"),
    url(r"^staff/filemanager/$", "app.views.staffFileManager"),
    url(r"^staff/fileupdate/", "app.views.fileUpdate"),
    url(r"^editor/$", "app.views.articleEditor", {'article_id':None}),
    url(r"^editor/(?P<article_id>\d+)/$", "app.views.articleEditor"),
    url(r"^editor/(?P<article_id>[\-\d\w]+)/autosave/$", "app.views.articleAutosave"),
    url(r"^editor/(?P<article_id>\d+)/picker/$", "app.views.imagePicker"),
    url(r"^editor/(?P<article_id>\d+)/preview", "app.views.article", {'type':'editorPreview'}),
    url(r"^editor/upload/$", "app.views.fileUpload", name="fileUpload"),
    url(r"^editor/upload/recent/$", "app.views.recentFiles", name="recentFiles"),
    url(r"^login/$", 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r"^logout/$", 'app.views.logout_view'),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
if ENVIRONMENT == 'DEV':
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': MEDIA_ROOT,
            }),
    )
