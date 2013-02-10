__author__ = 'jared'
from lgodimport.util import *
from app.models import *
from main.settings import MEDIA_ROOT
from os.path import exists

CATEGORIES = {
    'Games':'games',
    'Xbox 360':'xbox',
    'Playstation 3':'ps3',
    'PC Gaming':'pc',
    'Portable Gaming':'portable',
    'Tabletop Gaming':'tabletop',
    'Nintendo Wii':'wii',
    'Reviews':'gamereviews',
    'Upcoming':'upcoming',
    'Multi-platform':'multi-platform',
    'Industry':'industry',
    'Technology':'technology',
    'PC':'pctech',
    'Mobile':'mobile',
    'Apple':'apple',
    'Gadgets':'gadgets',
    'Internet':'web',
    'Opinion':'opinion',
    'Rants':'rants',
    'Copyright':'copyright',
    'Intellectual Property':'ip',
    'Public Policy':'public',
    'Speculation':'spec',
    'Privacy':'privacy',
    'Entertainment':'ent',
    'Movies':'movies',
    'Music':'music',
    'Books':'books',
    'Comics':'comix',
    'Television':'tv',
    'Web Comics':'web-comics',
    'Things We Like':'things-we-like',
    'Events':'events',
    'Conventions':'cons',
    'Releases':'releases',
    'Random':'random',
    'Meetup':'meetup',
    'Side Note':'side-note',
    'Information':'information',
    'Fun':'fun',
    'Basic':'basic',
    'Typography':'typography'
}

def setRedirect(oldarticle,narticle):
    oldid = oldarticle['id']
    newid = narticle.id
    redirect = URLRedirect.objects.get_or_create(oldid=oldid,newid=newid)
    redirect[0].save()


def importArticle(article):
    title = getTitle(article)
    createarticle = Article.objects.get_or_create(title=title)
    narticle = createarticle[0]
    narticle.summary = getSummary(article)
    narticle.body = getBody(article)
    if exists(MEDIA_ROOT+str(getImage(article))):
        narticle.image = importImage(article)
    if getCategory(article) == 'Side Note':
        narticle.type = 'sidebar'
    nslug = getCategory(article)
    try:
        narticle.categories.add(Category.objects.get(slug=nslug))
    except:
        print 'Could not add category '+nslug
    narticle.author = getAuthor(article)
    narticle.list_date = getPublishDate(article)
    narticle.date_posted = getPublishDate(article)
    status = getStatus(article)
    if status == 1:
        narticle.is_posted = 1
    narticle.save()
    setRedirect(article,narticle)


def importImage(article):
    if exists(MEDIA_ROOT+getImage(article)):
        timage = ArticleImage.objects.create(image=getImage(article))
        timage.save()
        timtype = ArticleImageType.objects.get(name='header')
        timcrop = ArticleImageCrop.objects.create(src=timage, type=timtype)
        timcrop.cropped_file = getImage(article)
        timcrop.URL = CDNUpload(timcrop.cropped_file)
        timcrop.save()
        timage.header = timcrop
        timage.thumbnail = timcrop
        timage.small_featured = timcrop
        timage.medium_featured = timcrop
        timage.small_header = timcrop
        timage.medium_header = timcrop
        timage.save()
        return timage
    else:
        return None