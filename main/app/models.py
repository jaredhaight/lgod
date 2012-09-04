from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, HiddenInput
from django.forms.models import modelformset_factory
from django import forms
from django.forms.widgets import  TextInput, SelectMultiple
from django.template.defaultfilters import slugify
from django.db.models import get_model
import cloudfiles
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
def testcats():
    i = 0
    while i < 30:
        cat = Category.objects.create()
        cat.name = 'test-'+str(i)
        cat.slug = cat.name
        cat.save()
        i = i+1

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

def resizeImage(image,):
    workimage = Image.open(image.article.image)
    box = (image.X, image.Y, image.X2, image.Y2)
    savestr = 'articles/'+str(image.article.id)+image.type+'.jpg'
    crop = workimage.crop(box)
    crop.save(MEDIA_ROOT+savestr, "JPEG")
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
    image = models.ImageField(upload_to="full_img")
    featured_image=models.ForeignKey('ArticleImage',related_name='featured_image', null=True, blank=True)
    header_image=models.ForeignKey('ArticleImage', related_name='header_image', null=True, blank=True)
    thumbnail=models.ForeignKey('ArticleImage', related_name='thumbnail', null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(Category)
    author = models.ForeignKey(User)
    edit_user = models.CharField(max_length=30)
    last_edited = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField()
    date_posted = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)
        if not self.title_slug:
            self.title_slug = uniqueSlug('Article','title_slug',self.title)
        if self.image and not self.thumbnail:
            self.header_image= ArticleImage.objects.create(article = self, type='header')
            self.featured_image = ArticleImage.objects.create(article = self, type='featured')
            self.thumbnail = ArticleImage.objects.create(article = self, type='thumbnail')
        super(Article, self).save(*args, **kwargs)

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ('title','summary','categories','type', 'body', 'image')
        widgets = {
            'title': TextInput(attrs={'class':'input-xlarge'}),
            'body': Textarea(attrs={'id':'editorBody'}),
            'summary':  Textarea(attrs={'id':'editorSummary'}),
            'categories': SelectMultiple(attrs={'id':'editorCategories'})
        }

class ArticleImage(models.Model):
    article = models.ForeignKey('Article')
    type = models.CharField(max_length=20, null=True, blank=True)
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
        if self.X:
            self.cropped_file = resizeImage(self)
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

class FileUpload(models.Model):
    file = models.FileField(upload_to="img/articles")
    title = models.CharField(max_length=50, null=True, blank=True)
    folder = models.CharField(max_length=50, null=True, blank=True)
    cdn_url = models.URLField()
    uploaded = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super(FileUpload, self).save(*args, **kwargs)
        self.cdn_url = CDNUpload(self.file)
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


