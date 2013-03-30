__author__ = 'jared'
from main.settings import NONSECURE_STATIC_URL, STATIC_URL, LOGIN_URL, ENVIRONMENT

def pass_environment(request):
    return { 'ENVIRONMENT': ENVIRONMENT}

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

def robots_ssl(request):
    if request.is_secure():
        return {'ROBOTS_META': 'none'}
    else:
        return {'ROBOTS_META': 'follow, index'}

def login_url(request):
    return {'LOGIN_URL': LOGIN_URL}