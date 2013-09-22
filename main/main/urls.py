from django.conf.urls import patterns, include, url
from app.feeds import lgodFeed
# Uncomment the next two lines to enable the admin:
# test comment
from django.contrib import admin
from main.settings import ENVIRONMENT, MEDIA_ROOT

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r'^search/', include('haystack.urls')),
    url(r'^archive/', 'app.views.archive', name='archive'),
    url(r"^category/(?P<jslug>[\-\d\w]+)/$", "app.views.category"),
    url(r"^article/(?P<article_id>[\-\d\w]+)/$", "app.views.article", {'type':'articleView'}),
    url(r"^author/(?P<jslug>[\-\d\w]+)/$", "app.views.authorPage"),
    url(r"^feed/", lgodFeed()),
    url(r"^about/$", "app.views.about"),
    url(r"^staff/$", "app.views.staffHome"),
    url(r"^staff/drafts/$", "app.views.staffDrafts"),
    url(r"^staff/profile/$", "app.views.profilePage"),
    url(r"^staff/image/(?P<image_id>\d+)/", "app.views.imageEditor"),
    url(r"^staff/image/upload/$","app.views.imageUpload"),
    url(r"^staff/images/$", "app.views.staffImages"),
    url(r"^staff/fileupdate/", "app.views.fileUpdate"),
    url(r"^staff/password/$", "app.views.change_password", {},'change_password'),
    url(r"^staff/password/done/$", 'app.views.password_change_done', name='change_password_done'),
    url(r"^editor/$", "app.views.articleEditor", {'article_id':None}),
    url(r"^editor/(?P<article_id>\d+)/$", "app.views.articleEditor"),
    url(r"^editor/(?P<article_id>[\-\d\w]+)/autosave/$", "app.views.articleAutosave"),
    url(r"^editor/(?P<article_id>\d+)/picker/$", "app.views.imagePicker"),
    url(r"^editor/(?P<article_id>\d+)/preview", "app.views.article", {'type':'editorPreview'}),
    url(r"^editor/(?P<article_id>\d+)/delete", "app.views.articleDelete"),
    url(r"^editor/upload/$", "app.views.fileUpload", name="fileUpload"),
    url(r"^editor/upload/recent/$", "app.views.recentFiles", name="recentFiles"),
    url(r"^login/$", 'app.views.login_view'),
    url(r"^logout/$", 'app.views.logout_view'),
    # Legacy URLs
    url(r'^games/(?P<subcat>[\-\d\w]*)/(?P<oldid>\d*)',"app.views.urlRedirect"),
    url(r'^technology/(?P<subcat>[\-\d\w]*)/(?P<oldid>\d*)',"app.views.urlRedirect"),
    url(r'^entertainment/(?P<subcat>[\-\d\w]*)/(?P<oldid>\d*)',"app.views.urlRedirect"),
    url(r'^events/(?P<subcat>[\-\d\w]*)/(?P<oldid>\d*)',"app.views.urlRedirect"),
    url(r'^opinion/(?P<subcat>[\-\d\w]*)/(?P<oldid>\d*)',"app.views.urlRedirect"),
    url(r"^article/(?P<article_id>[\-\d\w]+)/images/stories/(?P<imageString>.*$)", "app.views.legacyArticleImageRedirect"),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
handler404 = 'app.views.fourohfour'
handler403 = 'app.views.fourohthree'

if ENVIRONMENT == 'DEV':
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': MEDIA_ROOT,
            }),
    )
