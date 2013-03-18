__author__ = 'jared'
from main.settings import NONSECURE_STATIC_URL, STATIC_URL, LOGIN_URL

def manage_static_url(request):
    if not request.is_secure():
        return { 'STATIC_URL': NONSECURE_STATIC_URL }
    else:
        return { 'STATIC_URL': STATIC_URL}

def jared_css(request):
    try:
        style = request.GET['style']
    except:
        style = None
    return {'JSTYLE': style}

def login_url(request):
    return {'LOGIN_URL': LOGIN_URL}