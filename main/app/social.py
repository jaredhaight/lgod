# import required classes
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from main.settings import CLIENT_SECRETS, BASE_URL, GA_PROFILE_ID, LOGGING_DIR
import requests
import datetime


# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/analytics.readonly',
    redirect_uri='http://127.0.0.1')

# A file to store the access token
TOKEN_FILE_NAME = LOGGING_DIR+'analytics.dat'

def prepare_credentials():
    # Retrieve existing credendials
    storage = Storage(TOKEN_FILE_NAME)
    credentials = storage.get()

    # If existing credentials are invalid and Run Auth flow
    # the run method will store any new credentials
    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage) #run Auth Flow and store credentials

    return credentials

def initialize_service():
    # 1. Create an http object
    http = httplib2.Http()

    # 2. Authorize the http object
    # In this tutorial we first try to retrieve stored credentials. If
    # none are found then run the Auth Flow. This is handled by the
    # prepare_credentials() function defined earlier in the tutorial
    credentials = prepare_credentials()
    http = credentials.authorize(http)  # authorize the http object

    # 3. Build the Analytics Service Object with the authorized http object
    return build('analytics', 'v3', http=http)

service = initialize_service()

def get_google_stats(service, article):
    date_posted = article.date_posted.strftime('%Y-%m-%d')
    today = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    url = 'ga:pagePath==/article/'+article.title_slug+'/'
    # Use the Analytics Service Object to query the Core Reporting API
    return service.data().ga().get(
        ids='ga:' + GA_PROFILE_ID,
        start_date= date_posted,
        end_date=today,
        metrics='ga:pageviews',
        filters=url).execute()

def get_pageviews(google_stats):
    # Print data nicely for the user.
    if google_stats.get('rows'):
        return google_stats.get('rows')[0][0]
    else:
        return 0

def get_facebook_shares(article):
    url = BASE_URL+'article/'+article.title_slug+'/'
    r = requests.get('http://graph.facebook.com/'+url)
    try: shares = r.json['shares']
    except: shares = 0
    return shares

def get_twitter_stats(article):
    url = BASE_URL+'article/'+article.title_slug+'/'
    r = requests.get('http://urls.api.twitter.com/1/urls/count.json?url='+url)
    try: tweets = r.json['count']
    except: tweets = 0
    return tweets

def update_social_stats(article):
    stats = get_google_stats(service, article)
    article.social.pageviews = get_pageviews(stats)
    article.social.tweets = get_twitter_stats(article)
    article.social.facebook = get_facebook_shares(article)
    article.social.save()