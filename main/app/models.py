from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea
from django import forms
from django.forms.widgets import  TextInput, SelectMultiple
from django.template.defaultfilters import slugify
from django.forms import CheckboxSelectMultiple
from django.db.models import get_model
import cloudfiles
from main.settings import RACKSPACE_USER, RACKSPACE_API_KEY, RACKSPACE_MEDIA_CONTAINER


GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

# Create your models here.
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
        count = str(model.objects.filter(**kwargs).count())
        if count == '0':
            return slug
        else:
            slug = slug+'-'+count
            return slug

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=20)
    def __unicode__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=150)
    date_posted = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField()
    summary = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    title_slug = models.SlugField(null=True, blank=True, unique=True)
    header_image = models.ImageField(upload_to="header_imgs/")
    header_url = models.URLField()
    categories = models.ManyToManyField(Category)
    author = models.ForeignKey(User)
    edit_user = models.CharField(max_length=30)
    last_edited = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)
        if not self.header_url:
            self.header_url = CDNUpload(self.header_image)
        if not self.title_slug:
            self.title_slug = uniqueSlug('Article','title_slug',self.title)
        super(Article, self).save(*args, **kwargs)

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ('title','summary','categories','header_image','is_featured', 'body')
        widgets = {
            'title': TextInput(attrs={'class':'input-xlarge'}),
            'body': Textarea(attrs={'id':'editorBody'}),
            'summary':  Textarea(attrs={'id':'editorSummary'}),
            'categories': SelectMultiple(attrs={'id':'editorCategories'})
        }

class FileUpload(models.Model):
    file = models.FileField(upload_to="img/")
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


