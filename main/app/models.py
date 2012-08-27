from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.forms import ModelForm, Textarea
from django.template.defaultfilters import slugify
from django import forms
from django.forms.widgets import CheckboxSelectMultiple, TextInput
from django.forms.models import ModelMultipleChoiceField
import cloudfiles
from main.settings import RACKSPACE_USER, RACKSPACE_API_KEY, RACKSPACE_MEDIA_CONTAINER

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=150)
    date_posted = models.DateTimeField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    title_slug = models.SlugField(null=True, blank=True, unique=True)
    categories = models.ManyToManyField(Category)
    author = models.CharField(max_length=30)
    last_edited = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField()

    def __unicode__(self):
        return self.title
        
class ArticleForm(ModelForm):
    class Meta:
        model = Article
        exclude = ('title_slug','is_posted','author','date_posted','last_edited')
        widgets = {
            'title': TextInput(attrs={'class':'input-xlarge'}),
            'body': Textarea(attrs={'id':'editorBody'}),
            'summary':  Textarea(attrs={'id':'editorSummary'}),
        }

class FileUpload(models.Model):
    file = models.FileField(upload_to="img/")
    cdn_url = models.URLField()
    uploaded = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super(FileUpload, self).save(*args, **kwargs)
        conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY)
        cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
        obj = cont.create_object(self.file.name)
        obj.load_from_filename(self.file.path)
        self.cdn_url = obj.public_uri()
        self.save_base()

class StaffProfile(models.Model):
    user = models.OneToOneField(User)
    twitter = models.CharField(max_length=30)
    facebook = models.URLField()
    gplus = models.URLField()
    bio = models.TextField(null=True, blank=True)

class ProfileForm(ModelForm):
    twitter = forms.CharField(label='Twitter Username')
    facebook = forms.URLField(label='Facebook URL')
    gplus = forms.URLField(label='Google+ URL')
    
    class Meta:
        model = StaffProfile
        exclude = ('user')
        widgets = {
            'bio': Textarea(attrs={'id':'bioBody'}),
        }


