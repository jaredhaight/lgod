import httplib
from django.core.files.images import get_image_dimensions
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, HiddenInput, ChoiceField
from django.forms.models import modelformset_factory
from django import forms
from django.forms.widgets import  TextInput, SelectMultiple, RadioSelect
from django.template.defaultfilters import slugify
from django.db.models import get_model
import cloudfiles, time, hashlib, urllib, bleach
from PIL import Image
from main.settings import RACKSPACE_USER, RACKSPACE_API_KEY, RACKSPACE_MEDIA_CONTAINER, RACKSPACE_MEDIA_URL, MEDIA_ROOT, BASE_URL, STATIC_URL

GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

PROFILE_IMAGE_SOURCES = (
        ('gravatar', 'Gravatar'),
        ('facebook','Facebook')
)

ARTICLE_TYPE = (
        ('featured','Featured'),
        ('standard','Standard'),
        ('sidebar','Sidebar')
)

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

BLEACH_BODY_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'rel','target'],
    'img': ['src', 'alt', 'style'],
    'iframe': ['src','width','height','allowfullscreen','frameborder'],
}

BLEACH_BODY_TAGS = ['a','h2','h3','p', 'em', 'strong','li','ul','ol','del','blockquote','iframe','img','hr']
BLEACH_BODY_STYLE_ATTRIBUTES = ['float','margin','width']

BLEACH_MISC_ATTRIBUTES = {}
BLEACH_MISC_TAGS = []
# This is a function for testing.
def setupcats():
   for name,slug in CATEGORIES.items():
       cat = Category.objects.create()
       cat.name = name
       cat.slug = slug
       cat.save()

def setupImages():
    header = ArticleImage.objects.create(name='header', editable=True, width=1500, height=400)
    header.related = None
    header.save()

    thumb = ArticleImageType.objects.create(name='thumbnail', editable=False, width=400, height=400)
    thumb.related = ArticleImageType.objects.get(name='header')
    thumb.save()

    mediumHeader = ArticleImageType.objects.create(name='mediumHeader', editable=False, width=1125, height=300)
    mediumHeader.related = ArticleImageType.objects.get(name='header')
    mediumHeader.save()

    smallHeader = ArticleImageType.objects.create(name='smallHeader', editable=False, width=750, height=200)
    smallHeader.related = ArticleImageType.objects.get(name='header')
    smallHeader.save()


    mediumHeader = ArticleImageType.objects.create(name='mediumFeatured', editable=False, width=800, height=400)
    mediumHeader.related = ArticleImageType.objects.get(name='header')
    mediumHeader.save()

    smallHeader = ArticleImageType.objects.create(name='smallFeatured', editable=False, width=650, height=400)
    smallHeader.related = ArticleImageType.objects.get(name='header')
    smallHeader.save()


def CDNUpload(file):
    conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY, timeout=60)
    cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
    obj = cont.create_object(file.name)
    obj.load_from_filename(file.path)
    try: cdn_url = RACKSPACE_MEDIA_URL + str(file.name)
    except:
        cdn_url = RACKSPACE_MEDIA_URL + str(file.name)
    return cdn_url

def CDNDelete(file):
    conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY, timeout=60)
    cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
    cont.delete_object(file)

def uniqueSlug(model, id, slug_field, title):
    kwargs={}
    title = title[:48]
    last_space = title.rfind(' ')
    title = title[:last_space]
    slug = slugify(title)
    model = get_model('app',model)
    kwargs[slug_field] = slug
    count = model.objects.filter(**kwargs).exclude(id=id).count()
    if count == 0:
        return slug
    else:
        i = 1
        while count > 0:
            newslug = slug+'-'+str(i)
            kwargs[slug_field] = newslug
            count = model.objects.filter(**kwargs).exclude(id=id).count()
            i = i+1
        return newslug

def resizeImage(src, image, width, height):
    workimage = Image.open(open(image.path, 'rb'))
    timestamp = time.strftime('%y%m%d%H%M%S')
    savestr = 'articles/'+timestamp+src+'.jpg'

    if height == 0:
        height = workimage.size[1] * width / workimage.size[0]

    resize = workimage.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=85)
    return savestr

def cropImage(image):
    workimage = Image.open(image.src.image.path)
    width = image.type.width
    height = image.type.height
    box = (image.X, image.Y, image.X2, image.Y2)
    timestamp = time.strftime('%y%m%d%H%M%S')
    savestr = 'articles/'+timestamp+str(image.src.id)+image.type.name+'.jpg'
    crop = workimage.crop(box)
    resize = crop.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=85)
    print savestr
    return savestr

def trimImage(articleImageCrop,type,size):
    workimage = Image.open(articleImageCrop.cropped_file.path)
    x = size
    x2 = (workimage.size[0] - size)
    box = (x, 0 , x2, workimage.size[1])
    timestamp = time.strftime('%y%m%d%H%M%S')
    savestr = 'articles/'+timestamp+type+'.jpg'
    trim = workimage.crop(box)
    trim.save(MEDIA_ROOT+savestr, "JPEG", quality=85)
    return savestr


def connectCrops(article_id,image_id):
    article = Article.objects.get(pk=article_id)
    image = ArticleImage.objects.get(pk=image_id)
    article.image = image
    article.save()

def purgeCache():
    conn = httplib.HTTPConnection('localhost')
    conn.request('BAN','/')
    resp = conn.getresponse()
    return {'status':resp.status, 'response':resp.read()}

class URLRedirect(models.Model):
    oldid = models.IntegerField(max_length=10)
    newid = models.IntegerField(max_length=10)

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=20)
    def __unicode__(self):
        return self.name

class Article(models.Model):
    type = models.CharField(max_length=20, choices=ARTICLE_TYPE, default='standard')
    title = models.CharField(max_length=150)
    title_slug = models.SlugField(null=True, blank=True, unique=True)
    image = models.ForeignKey('ArticleImage', related_name='article_image', null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(Category, null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="author")
    edit_user = models.ForeignKey(User, null=True, blank=True, related_name="edit_user")
    last_edited = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField()
    date_posted = models.DateTimeField(null=True, blank=True)
    social = models.ForeignKey('ArticleSocialStats', related_name='social_stats', null=True, blank=True)
    list_date = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.title

    def post_status(self):
        errors = []
        status = 'not_ready'

        if not self.body:
            errors.append('Article has no content')

        if self.type != 'sidebar' and not self.summary:
            errors.append('Article has no summary')

        if self.type != 'sidebar' and not self.image:
            errors.append('Article does not have an image')

        if self.type != 'sidebar' and self.categories.count() < 1:
            errors.append('Article is not categorized')

        if self.is_posted:
            status = 'posted'
        elif not errors:
            status = 'ready_to_post'

        return status, errors

    def get_absolute_url(self):
        return BASE_URL+'article/'+self.title_slug


    def save(self, *args, **kwargs):
        if not self.is_posted:
            self.is_posted = False
            self.title_slug = uniqueSlug('Article',self.id,'title_slug',self.title)
        else:
            purge = purgeCache()
            print str(purge)
        self.title = bleach.clean(self.title, BLEACH_MISC_TAGS, BLEACH_MISC_ATTRIBUTES, strip=True)
        self.summary = bleach.clean(self.summary, BLEACH_MISC_TAGS, BLEACH_MISC_ATTRIBUTES, strip=True)
        self.body = bleach.clean(self.body,BLEACH_BODY_TAGS,BLEACH_BODY_ATTRIBUTES,BLEACH_BODY_STYLE_ATTRIBUTES)
        super(Article, self).save(*args, **kwargs)
        if not self.social:
            social = ArticleSocialStats.objects.create()
            self.social = social
        super(Article, self).save(*args, **kwargs)

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ('title','title_slug','summary','categories','type', 'body')
        widgets = {
            'title_slug': HiddenInput(),
            'title': TextInput(attrs={'class':'input-xlarge'}),
            'body': Textarea(attrs={'id':'editorBody'}),
            'summary':  Textarea(attrs={'id':'editorSummary'}),
            'categories': SelectMultiple(attrs={'id':'editorCategories'})
        }

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.fields['categories'].queryset = Category.objects.order_by('name')

class ArticleSocialStats(models.Model):
    pageviews = models.BigIntegerField(max_length=10, null=True, blank=True)
    pv_date_updated = models.DateTimeField(null=True, blank=True)
    tweets = models.BigIntegerField(max_length=10, null=True, blank=True)
    tweets_date_updated = models.DateTimeField(null=True, blank=True)
    facebook = models.BigIntegerField(max_length=10, null=True, blank=True)
    facebook_date_updated = models.DateTimeField(null=True, blank=True)

class ArticleImageType(models.Model):
    name = models.CharField(max_length=20, null=True, blank=True)
    editable = models.BooleanField()
    related = models.ForeignKey('ArticleImageType', related_name='related_crop', null=True, blank=True)
    width = models.IntegerField(max_length=5)
    height = models.IntegerField(max_length=5)

    def __unicode__(self):
        return self.name

class ArticleImage(models.Model):
    image = models.ImageField(upload_to="full_img", null=True, blank=True)
    header=models.ForeignKey('ArticleImageCrop', related_name='header_image', null=True, blank=True)
    small_header = models.ForeignKey('ArticleImageCrop', related_name='small_header_image', null=True, blank=True)
    medium_header = models.ForeignKey('ArticleImageCrop', related_name='medium_header_image', null=True, blank=True)
    thumbnail = models.ForeignKey('ArticleImageCrop', related_name='thumbnail', null=True, blank=True)
    small_featured = models.ForeignKey('ArticleImageCrop', related_name='small_featured', null=True, blank=True)
    medium_featured = models.ForeignKey('ArticleImageCrop', related_name='medium_featured', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

    def admin_thumbnail(self):
        return u'<img style="width:200px;" src="%s"/>'% (self.thumbnail.URL)
    admin_thumbnail.short_description  = 'Thumbnail'
    admin_thumbnail.allow_tags = True

    def __unicode__(self):
        return str(self.id)


class ArticleImageForm(ModelForm):
    class Meta:
        model = ArticleImage
        fields = ('image','description')
    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            raise forms.ValidationError("No image!")
        else:
            w, h = get_image_dimensions(image)
            if w < 1500:
                raise forms.ValidationError("The image is %i pixel wide. It's supposed to be 1500px" % w)
            if h < 400:
                raise forms.ValidationError("The image is %i pixel high. It's supposed to be 600px" % h)
        return image

class ArticleImageCrop(models.Model):
    src = models.ForeignKey('ArticleImage')
    type = models.ForeignKey('ArticleImageType')
    X = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    Y = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    X2 = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    Y2 = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    cropped_file = models.FileField(upload_to='img/articles', null=True, blank=True)
    URL = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return str(self.id)

    def CDN_URL(self):
        return RACKSPACE_MEDIA_URL + str(self.cropped_file)

    def save(self, *args, **kwargs):
        super(ArticleImageCrop, self).save(*args, **kwargs)
        if self.X2:
            if self.URL:
                try: CDNDelete(self.cropped_file)
                except: pass
            articleImage = ArticleImage.objects.get(id = self.src.id)
            self.cropped_file = cropImage(self)
            self.URL = CDNUpload(self.cropped_file)
            super(ArticleImageCrop, self).save(*args, **kwargs)
            if self.type.name == 'header':
                articleImage.header = self
                articleImage.save()

                smallFeatured = ArticleImageType.objects.get(name='smallFeatured')
                size = (self.type.width - smallFeatured.width) / 2
                image = trimImage(self, smallFeatured.name, size)
                crop = ArticleImageCrop.objects.get(src=self.src, type=smallFeatured)
                if crop.URL:
                    try: CDNDelete(crop.cropped_file)
                    except: pass
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.small_featured = crop

                mediumFeatured = ArticleImageType.objects.get(name='mediumFeatured')
                size = (self.type.width - mediumFeatured.width) / 2
                image = trimImage(self, mediumFeatured.name, size)
                crop = ArticleImageCrop.objects.get(src=self.src, type=mediumFeatured)
                if crop.URL:
                    try: CDNDelete(crop.cropped_file)
                    except: pass
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.medium_featured = crop

                thumbnail = ArticleImageType.objects.get(name='thumbnail')
                size = (self.type.width - thumbnail.width) / 2
                image = trimImage(self, thumbnail.name, size)
                crop = ArticleImageCrop.objects.get(src=self.src, type=thumbnail)
                if crop.URL:
                    try: CDNDelete(crop.cropped_file)
                    except: pass
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.thumbnail = crop

                smallHeader = ArticleImageType.objects.get(name='smallHeader')
                image = resizeImage(smallHeader.name, self.cropped_file, smallHeader.width, smallHeader.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=smallHeader)
                if crop.URL:
                    try: CDNDelete(crop.cropped_file)
                    except: pass
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.small_header = crop

                mediumHeader = ArticleImageType.objects.get(name='mediumHeader')
                image = resizeImage(mediumHeader.name, self.cropped_file, mediumHeader.width, mediumHeader.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=mediumHeader)
                if crop.URL:
                    try: CDNDelete(crop.cropped_file)
                    except: pass
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.medium_header = crop
            articleImage.save()
            super(ArticleImageCrop, self).save(*args, **kwargs)

    def delete(self):
        CDNDelete(self.cropped_file)
        super(ArticleImageCrop, self).delete()

@receiver(post_delete, sender=ArticleImageCrop)
def _articleimagecrop_delete(sender, instance, **kwargs):
    CDNDelete(instance.cropped_file)


class ArticleImageCropForm(ModelForm):
    class Meta:
        model= ArticleImageCrop
        fields = ('type','X','Y','X2','Y2')
        widgets = {
            'type': HiddenInput(),
            'X': HiddenInput(attrs={'id':'X'}),
            'Y': HiddenInput(attrs={'id':'Y'}),
            'X2':  HiddenInput(attrs={'id':'X2'}),
            'Y2': HiddenInput(attrs={'id':'Y2'}),
        }

imageFormset = modelformset_factory(ArticleImageCrop, form=ArticleImageCropForm, extra=0)

class ContentImage(models.Model):
    image = models.ImageField(upload_to="img/content")
    title = models.CharField(max_length=50, null=True, blank=True)
    folder = models.CharField(max_length=50, null=True, blank=True)
    cdn_url = models.URLField()
    uploaded = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super(ContentImage, self).save(*args, **kwargs)
        if self.image.width > 800:
            self.image = resizeImage('ac', self.image, 800, 0)
        self.cdn_url = CDNUpload(self.image)
        self.save_base()

class StaffProfile(models.Model):
    user = models.OneToOneField(User)
    displayName = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    imageType = models.CharField(max_length=15, choices=PROFILE_IMAGE_SOURCES)
    imageURL = models.URLField(null=True, blank=True)
    twitter = models.CharField(max_length=30, null=True,  blank=True)
    facebook = models.URLField(null=True,  blank=True)
    gplus = models.URLField(null=True,  blank=True)
    purl_name = models.CharField(max_length=30, null=True,  blank=True)
    purl = models.URLField(null=True,  blank=True)
    bio = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.displayName

    def save(self, *args, **kwargs):
        print 'Saving Profile Model'
        if self.imageType == 'facebook' and self.facebook:
            fbindex = self.facebook.index('.com/')+5
            fbuser = self.facebook[fbindex:].strip('/')
            self.imageURL = 'http://graph.facebook.com/'+fbuser+'/picture/?type=large'
        elif self.imageType == 'twitter' and self.twitter:
            twituser = self.twitter.strip('@')
            self.imageURL = 'https://api.twitter.com/1/users/profile_image?screen_name='+twituser+'&size=original'
        else:
            self.imageType = 'gravatar'
            default = 'http://ace9a87d776422b2d1ab-2b334246b9b35e4c2de9424cd61cfe99.r33.cf2.rackcdn.com/img/default.png'
            size = 200
            gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.user.email.lower()).hexdigest() + "?" + urllib.urlencode({'d':default, 's':str(size)})
            self.imageURL = gravatar_url
        super(StaffProfile, self).save(*args, **kwargs)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name','email')
        
class ProfileForm(ModelForm):
    displayName = forms.CharField(label='Display Name')
    twitter = forms.CharField(label='Twitter Username', required=False)
    facebook = forms.URLField(label='Facebook URL', required=False)
    gplus = forms.URLField(label='Google+ URL', required=False)
    purl_name = forms.CharField(label='Website Name', required=False)
    purl = forms.URLField(label='Website URL', required=False)
    imageType = forms.ChoiceField(label='Profile Image Source', choices=PROFILE_IMAGE_SOURCES)
    
    class Meta:
        model = StaffProfile
        exclude = ('user','imageURL')
        widgets = {
            'bio': Textarea(attrs={'id':'bioBody'}),
        }


