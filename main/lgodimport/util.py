__author__ = 'jared'
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from main.settings import DBROOTPWD

conn = create_engine('mysql://root:%s@127.0.0.1/lgod_old' % DBROOTPWD)

AUTHORS ={
    'admin':'admin',
    'Colin':'colin',
    'Juan':'juan',
    'Justin':'justin',
    'Matt':'matt',
    'Murphinator2000':'murph',
    'photosandtext':'jared',
    'SarahB':'sarahb',
    'shamblett':'sean',
    'WedgeRed2':'ken',
    'adamj':'adamj',
    'AaronOutspoken':'aaron',
    'amy':'amy',
    'bstumpf':'bstumpf',
    'Dave D':'daved'
}


def getArticles():
    articles = []
    for row in conn.execute('select c.id, c.title as title, cats.alias as category, c.alias, u.name, u.username, c.introtext, c.fulltext, c.publish_up, c.state from `#__content` as c inner join `#__assets` as assets on c.asset_id = assets.id inner join `#__categories` as cats on cats.id = c.catid inner join `#__users` as u on c.`created_by` = u.id where c.publish_up < "2013-02-01 00:00:00" order by c.publish_up'):
        articles.append(dict(row))
    return articles

#70 some odd articles didn't import properly because of a bug in getBody.
def getProbArticles():
    articles = []
    for row in conn.execute('select c.id, c.title as title, cats.alias as category, c.alias, u.name, u.username, c.introtext, c.fulltext, c.publish_up, c.state from `#__content` as c inner join `#__assets` as assets on c.asset_id = assets.id inner join `#__categories` as cats on cats.id = c.catid inner join `#__users` as u on c.`created_by` = u.id where c.id in (379, 451, 495, 600, 563, 684, 709, 655, 396, 671, 79, 699, 20, 547, 687, 128, 708, 480, 570, 660, 705, 112, 72, 605, 567, 215, 630, 155, 609, 623, 636, 558, 511, 214, 313, 378, 371, 239, 119, 246, 136, 779, 586, 698, 414, 661, 492, 668, 615, 562, 974, 543, 641, 489, 404, 504, 422, 524, 644, 523, 561, 629, 695, 468, 513, 512, 696, 260, 230, 182, 106, 106, 108, 80, 102, 295) order by c.publish_up'):
        articles.append(dict(row))
    return articles

def getTitle(article):
    print 'getTitle called. Returning '+article['title']
    return article['title']

def getSlug(article):
    return article['alias']

def getAuthor(article):
    og = article['username']
    print 'getAuthor called. Returning '+article['username']
    ng = AUTHORS.get(og)
    author = User.objects.get(username=ng)
    return author

def getImage(article):
    soup = BeautifulSoup(article['introtext'])
    image = soup.img
    if image:
        print 'getImage called. Returning '+soup.img['src']
        image = soup.img['src']
        slash = image.rfind('stories/')
        image = 'lgod_old' + image[slash+7:]
    else:
        print 'getImage called. No image found for article id '+str(article['id'])
    return image

def getSummary(article):
    soup = BeautifulSoup(article['introtext'])
    summary = soup.get_text(' ','\n')
    print 'getSummary called. Returning '+summary
    if len(summary) > 160:
        tsum = summary[:159]
        lastspace = tsum.rfind(' ')
        summary = tsum[:lastspace] + '...'
    return summary

def getPublishDate(article):
    print 'getPublishDate called. Returning '+str(article['publish_up'])
    return article['publish_up']

def getCategory(article):
    return article['category']

def getBody(article):
    print 'getBody called.'
    soup = BeautifulSoup(article['introtext'])
    list = soup.find_all('p')
    summary = ''
    for p in list:
        if not p.img:
            summary = summary+str(p.prettify(formatter='html'))
    if summary == '':
        summary = soup.prettify(formatter='html')
    if article['fulltext']:
        soup = BeautifulSoup(article['fulltext'])
        body = soup.prettify(formatter='html')
        print 'getBody got summary and body'
        return (summary + body)
    else:
        print 'getBody got summary only'
        return summary

def getStatus(article):
    print 'getStatus called. Returning '+str(article['state'])
    return article['state']
