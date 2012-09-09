from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, HiddenInput, FileInput
from django.forms.models import modelformset_factory
from django import forms
from django.forms.widgets import  TextInput, SelectMultiple
from django.template.defaultfilters import slugify
from django.db.models import get_model
import cloudfiles
import time
from PIL import Image
from main.settings import RACKSPACE_USER, RACKSPACE_API_KEY, RACKSPACE_MEDIA_CONTAINER, MEDIA_ROOT


GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

ARTICLE_TYPE = (
        ('featured','Featured'),
        ('standard','Standard'),
        ('sidebar','Sidebar')
)
# This is a function for testing. It creates thirty categories.
def setupcats():
    i = 0
    while i < 30:
        cat = Category.objects.create()
        cat.name = 'test-'+str(i)
        cat.slug = cat.name
        cat.save()
        i = i+1

    featured = ArticleImageType.objects.create(name='featured', width=400, height=400)
    featured.save()

    header = ArticleImageType.objects.create(name='header', width=1000, height=250)
    header.save()

    thumb = ArticleImageType.objects.create(name='thumbnail', width=125, height=125)
    thumb.save()

def CDNUpload(file):
    conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY)
    cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
    obj = cont.create_object(file.name)
    obj.load_from_filename(file.path)
    cdn_url = obj.public_uri()
    return cdn_url

def uniqueSlug(model, slug_field, title):
    kwargs={}
    slug = slugify(title)
    model = get_model('app',model)
    kwargs[slug_field] = slug
    count = model.objects.filter(**kwargs).count()
    if count == 0:
        return slug
    else:
        i = 1
        while count > 0:
            newslug = slug+'-'+str(i)
            kwargs[slug_field] = newslug
            count = model.objects.filter(**kwargs).count()
            i = i+1
        return newslug

def resizeImage(image, width, height):
    workimage = Image.open(image)
    timestamp = time.strftime('%m%d%y%H%M%S')
    savestr = 'articles/'+timestamp+'.jpg'

    if height == 0:
        height = workimage.size[1] * width / workimage.size[0]

    resize = workimage.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=95)
    return savestr

def cropImage(image):
    workimage = Image.open(image.article.image)
    width = image.type.width
    height = image.type.height
    box = (image.X, image.Y, image.X2, image.Y2)
    timestamp = time.strftime('%m%d%y%H%M%S')
    savestr = 'articles/'+timestamp+str(image.article.id)+image.type.name+'.jpg'
    crop = workimage.crop(box)
    resize = crop.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=95)
    return savestr


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=20)
    def __unicode__(self):
        return self.name

class Article(models.Model):
    type = models.CharField(max_length=20, choices=ARTICLE_TYPE, default='standard')
    title = models.CharField(max_length=150)
    title_slug = models.SlugField(null=True, blank=True, unique=True)
    image = models.ImageField(upload_to="full_img", null=True, blank=True)
    featured_image=models.ForeignKey('ArticleImage',related_name='featured_image', null=True, blank=True)
    header_image=models.ForeignKey('ArticleImage', related_name='header_image', null=True, blank=True)
    thumbnail=models.ForeignKey('ArticleImage', related_name='thumbnail', null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(Category, null=True, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, related_name="author")
    edit_user = models.ForeignKey(User, null=True, blank=True, related_name="edit_user")
    last_edited = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField()
    date_posted = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.title

    def post_status(self):
        errors = []
        status = 'not_ready'

        if not self.summary:
            errors.append('Article has no summary')

        if not self.body:
            errors.append('Article has no content')

        if self.type != 'sidebar' and self.categories.count() < 1:
            errors.append('Article is not categorized')

        if self.type != 'sidebar' and not self.image:
            errors.append("Article does not have an image")
            return status, errors

        if self.type != 'sidebar' and not self.thumbnail.URL:
            errors.append("Article does not have a thumbnail")

        if self.type != 'sidebar' and not self.header_image.URL:
            errors.append('Article does not have a header image.')

        if self.type == 'featured' and not self.featured_image.URL:
            errors.append('Article is Featured, but does not have a featured image')

        if self.is_posted == True:
            status = 'posted'
        elif not errors:
            status = 'ready_to_post'

        return status, errors

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)
        if not self.title_slug:
            self.title_slug = uniqueSlug('Article','title_slug',self.title)
        if self.image and not self.thumbnail:
            if self.image.width > 1000:
                self.image  = resizeImage(self.image.path, 1000, 0)
            self.header_image= ArticleImage.objects.create(article = self, type=(ArticleImageType.objects.get(name='header')))
            self.featured_image = ArticleImage.objects.create(article = self, type=(ArticleImageType.objects.get(name='featured')))
            self.thumbnail = ArticleImage.objects.create(article = self, type=(ArticleImageType.objects.get(name='thumbnail')))
        super(Article, self).save(*args, **kwargs)

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ('title','title_slug','summary','categories','type', 'body', 'image')
        widgets = {
            'title_slug': HiddenInput(),
            'title': TextInput(attrs={'class':'input-xlarge'}),
            'image': FileInput(),
            'body': Textarea(attrs={'id':'editorBody'}),
            'summary':  Textarea(attrs={'id':'editorSummary'}),
            'categories': SelectMultiple(attrs={'id':'editorCategories'})
        }

class ArticleImageType(models.Model):
    name = models.CharField(max_length=20, null=True, blank=True)
    width = models.IntegerField(max_length=5)
    height = models.IntegerField(max_length=5)

    def __unicode__(self):
        return self.name

class ArticleImage(models.Model):
    article = models.ForeignKey('Article')
    type = models.ForeignKey('ArticleImageType')
    X = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    Y = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    X2 = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    Y2 = models.DecimalField(max_digits=60, decimal_places=30, null=True, blank=True)
    cropped_file = models.FileField(upload_to='img/articles', null=True, blank=True)
    URL = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super(ArticleImage, self).save(*args, **kwargs)
        if self.X2:
            self.cropped_file = cropImage(self)
            self.URL = CDNUpload(self.cropped_file)
            super(ArticleImage, self).save(*args, **kwargs)


class ArticleImageForm(ModelForm):
    class Meta:
        model= ArticleImage
        fields = ('type','X','Y','X2','Y2')
        widgets = {
            'type': HiddenInput(),
            'X': HiddenInput(attrs={'id':'X'}),
            'Y': HiddenInput(attrs={'id':'Y'}),
            'X2':  HiddenInput(attrs={'id':'X2'}),
            'Y2': HiddenInput(attrs={'id':'Y2'}),
        }

imageFormset = modelformset_factory(ArticleImage, form=ArticleImageForm, extra=0)

class ArticleImageUpload(models.Model):
    image = models.ImageField(upload_to="img/articles")
    title = models.CharField(max_length=50, null=True, blank=True)
    folder = models.CharField(max_length=50, null=True, blank=True)
    cdn_url = models.URLField()
    uploaded = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super(ArticleImageUpload, self).save(*args, **kwargs)
        if self.image.width > 400:
            self.image = resizeImage(self.image.path, 400, 0)
        if self.image.height > 400:
            self.image = resizeImage(self.image.path, 0, 400)

        self.cdn_url = CDNUpload(self.image)
        self.save_base()

class StaffProfile(models.Model):
    user = models.OneToOneField(User)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    twitter = models.CharField(max_length=30, null=True,  blank=True)
    facebook = models.URLField(null=True,  blank=True)
    gplus = models.URLField(null=True,  blank=True)
    purl_name = models.CharField(max_length=30, null=True,  blank=True)
    purl = models.URLField(null=True,  blank=True)
    bio = models.TextField(null=True, blank=True)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'email')
        
class ProfileForm(ModelForm):
    twitter = forms.CharField(label='Twitter Username', required=False)
    facebook = forms.URLField(label='Facebook URL', required=False)
    gplus = forms.URLField(label='Google+ URL', required=False)
    purl_name = forms.CharField(label='Website Name', required=False)
    purl = forms.URLField(label='Website URL', required=False)
    
    class Meta:
        model = StaffProfile
        exclude = ('user')
        widgets = {
            'bio': Textarea(attrs={'id':'bioBody'}),
        }


