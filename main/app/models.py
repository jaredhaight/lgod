from django.core.files.images import get_image_dimensions
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
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

    header = ArticleImageType.objects.create(name='header', editable=True, width=1500, height=400)
    header.related = None
    header.save()

    thumb = ArticleImageType.objects.create(name='thumbnail', editable=True, width=750, height=450)
    thumb.related = None
    thumb.save()

    mediumHeader = ArticleImageType.objects.create(name='mediumHeader', editable=False, width=1125, height=300)
    mediumHeader.related = ArticleImageType.objects.get(name='header')
    mediumHeader.save()

    smallHeader = ArticleImageType.objects.create(name='smallHeader', editable=False, width=750, height=200)
    smallHeader.related = ArticleImageType.objects.get(name='header')
    smallHeader.save()

    mediumThumb = ArticleImageType.objects.create(name='mediumThumb', editable=False, width=500, height=300)
    mediumThumb.related = ArticleImageType.objects.get(name='thumbnail')
    mediumThumb.save()

    smallThumb = ArticleImageType.objects.create(name='smallThumb', editable=False, width=300, height=180)
    smallThumb.related = ArticleImageType.objects.get(name='thumbnail')
    smallThumb.save()


def CDNUpload(file):
    conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY)
    cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
    obj = cont.create_object(file.name)
    obj.load_from_filename(file.path)
    cdn_url = obj.public_uri()
    return cdn_url

def CDNDelete(file):
    conn = cloudfiles.Connection(RACKSPACE_USER,RACKSPACE_API_KEY)
    cont = conn.get_container(RACKSPACE_MEDIA_CONTAINER)
    cont.delete_object(file)

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

def resizeImage(src, image, width, height):
    workimage = Image.open(open(image.path, 'rb'))
    timestamp = time.strftime('%m%d%y%H%M%S')
    savestr = 'articles/'+timestamp+src+'.jpg'

    if height == 0:
        height = workimage.size[1] * width / workimage.size[0]

    resize = workimage.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=95)
    return savestr

def cropImage(image):
    workimage = Image.open(image.src.image)
    width = image.type.width
    height = image.type.height
    box = (image.X, image.Y, image.X2, image.Y2)
    timestamp = time.strftime('%m%d%y%H%M%S')
    savestr = 'articles/'+timestamp+str(image.src.id)+image.type.name+'.jpg'
    crop = workimage.crop(box)
    resize = crop.resize((width,height), Image.ANTIALIAS)
    resize.save(MEDIA_ROOT+savestr, "JPEG", quality=95)
    print savestr
    return savestr

def connectCrops(article_id,image_id):
    article = Article.objects.get(pk=article_id)
    image = ArticleImage.objects.get(pk=image_id)
    article.image = image
    article.save()


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

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)
        if not self.is_posted:
            self.title_slug = uniqueSlug('Article','title_slug',self.title)
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
    small_thumbnail = models.ForeignKey('ArticleImageCrop', related_name='small_thumbnail', null=True, blank=True)
    medium_thumbnail = models.ForeignKey('ArticleImageCrop', related_name='medium_thumbnail', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

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
            if h < 600:
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

    def save(self, *args, **kwargs):
        super(ArticleImageCrop, self).save(*args, **kwargs)
        if self.X2:
            articleImage = ArticleImage.objects.get(id = self.src.id)
            self.cropped_file = cropImage(self)
            self.URL = CDNUpload(self.cropped_file)
            if self.type.name == 'header':
                articleImage.header = self
                smallHeader = ArticleImageType.objects.get(name='smallHeader')
                image = resizeImage(smallHeader.name, self.cropped_file, smallHeader.width, smallHeader.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=smallHeader)
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.small_header = crop

                mediumHeader = ArticleImageType.objects.get(name='mediumHeader')
                image = resizeImage(mediumHeader.name, self.cropped_file, mediumHeader.width, mediumHeader.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=mediumHeader)
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.medium_header = crop

            if self.type.name == 'thumbnail':
                articleImage.thumbnail = self
                smallThumb = ArticleImageType.objects.get(name='smallThumb')
                image = resizeImage(smallThumb.name, self.cropped_file, smallThumb.width, smallThumb.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=smallThumb)
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.small_thumbnail = crop

                mediumThumb = ArticleImageType.objects.get(name='mediumThumb')
                image = resizeImage(mediumThumb.name, self.cropped_file, mediumThumb.width, mediumThumb.height)
                crop = ArticleImageCrop.objects.get(src=self.src, type=mediumThumb)
                crop.cropped_file = image
                crop.save()
                url = CDNUpload(crop.cropped_file)
                crop.URL = url
                crop.save()
                articleImage.medium_thumbnail = crop
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
        if self.image.height > 800:
            self.image = resizeImage('ac', self.image, 0, 800)

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


