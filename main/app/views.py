# Create your views here.
from django.contrib.auth import logout
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import datetime
import json
import logging
from app.models import *

logger = logging.getLogger(__name__)

def home(request):
    user = request.user
    articles = get_list_or_404(Article.objects.filter(is_posted=True).order_by("-date_posted"))
    features = Article.objects.filter(is_posted=True,type='featured').order_by("-date_posted")[:10]
    paginator = Paginator(articles, 9)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, features=features, user=user)
    return render_to_response("home.html", d)

def category(request, jslug):
    user = request.user
    articles = get_list_or_404(Article.objects.filter(categories__slug=jslug, is_posted=True).order_by("-date_posted"))
    paginator = Paginator(articles, 9)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, features=features, user=user)
    return render_to_response("home.html", d)
    
def authorPage(request, jslug):
    social = None
    user = request.user
    staff = get_object_or_404(User, username__iexact=str(jslug))
    articles = get_list_or_404(Article.objects.filter(author__username=jslug, is_posted=True).order_by("-date_posted"))
    
    try: staffProfile = StaffProfile.objects.get(user=User.objects.get(username=jslug))
    except: staffProfile = None
    
    if staffProfile.twitter or staffProfile.facebook or staffProfile.gplus:
        social = 'social'

    paginator = Paginator(articles, 9)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, staff=staff, staffProfile=staffProfile, social=social, user=user)
    return render_to_response("authorPage.html", d)
    
def article(request, article_id, type):
    user = request.user
    posted = None
    pagetype = 'article'

    if type=='editorPreview' and request.user.is_authenticated():
        article = get_object_or_404(Article, id=article_id)
    else:
        article = get_object_or_404(Article, title_slug=str(article_id), is_posted=True)
    
    if article.is_posted:
        posted = 'posted'

    d = dict(user=user,article=article, posted=posted, pagetype=pagetype)
    return render_to_response("articleView.html", d)

@csrf_exempt
@login_required
def articleEditor(request, article_id):
    user = request.user
    posted = None
    errors = None
    status = "new"
    if article_id:
        article = get_object_or_404(Article, pk=article_id)
        status, errors = article.post_status()

    else:
        article = None

    if request.method == 'POST':
        if "discard_article" in request.POST:
            return HttpResponseRedirect('/staff')
        else:
            try: article = Article.objects.get(pk=article_id)
            except:
                article = None
            form = ArticleForm(request.POST, request.FILES, instance=article)
            if form.is_valid():
                article = form.save(commit=False)
                if "post_article" in request.POST:
                    now = datetime.datetime.now()
                    article.date_posted = now.strftime("%Y-%m-%dT%H:%M:%S")
                    article.author = user
                    article.is_posted = True
                elif "unpost_article" in request.POST:
                    article.is_posted = False
                article.edit_user = user
                article.save()
                form.save_m2m()
                if "pick_photo" in request.POST:
                    return HttpResponseRedirect('/editor/'+str(article.id)+'/picker')
                if "update_article" in request.POST:
                    return HttpResponseRedirect('/editor/'+str(article.id))
                if "preview_article" in request.POST:
                    return HttpResponseRedirect('/editor/'+str(article.id)+'/preview')
                if "edit_photos" in request.POST:
                    return HttpResponseRedirect('/editor/'+str(article.id)+'/image')
                elif article.is_posted:
                    return HttpResponseRedirect('/article/'+article.title_slug)
                else:
                    return HttpResponseRedirect('/editor/'+str(article.id)+'/preview')
            
    else:
        form = ArticleForm(instance=article)

    return render_to_response("articleEditor.html", {
        'form': form,
        'article' : article,
        'posted' : posted,
        'user' : user,
        'status':status,
        'errors':errors},
        context_instance=RequestContext(request))

@login_required
def imageEditor(request,image_id):
    pagetype = 'article'
    articleImage = get_object_or_404(ArticleImage, id=image_id)
    featuredType = ArticleImageType.objects.get(name='featured')
    headerType = ArticleImageType.objects.get(name='header')
    thumbType = ArticleImageType.objects.get(name='thumbnail')
    featured = ArticleImageCrop.objects.get(type=featuredType.id, src=articleImage.id)
    header = ArticleImageCrop.objects.get(type=headerType.id, src=articleImage.id)
    thumb = ArticleImageCrop.objects.get(type=thumbType.id, src=articleImage.id)
    formset = imageFormset(queryset=ArticleImageCrop.objects.filter(src=articleImage.id))

    try:
        article_id = request.GET['article']
    except:
        article_id = None

    if request.method == "POST":
        try:
            article_id = request.GET['article']
        except:
            article_id = None

        formset = imageFormset(request.POST)
        if formset.is_valid():
            formset.save()

        if article_id:
            return HttpResponseRedirect('/editor/'+str(article_id))
        else:
            return HttpResponseRedirect('/staff/images')

    #Get width for image display
    ratio = articleImage.image.width/float(articleImage.image.height)
    imgheight = 1140/ratio

    return render_to_response("imageEditor.html", {
        'formset': formset,
        'articleImage': articleImage,
        'featuredType': featuredType,
        'headerType': headerType,
        'thumbType': thumbType,
        'featured':featured,
        'header': header,
        'thumb':thumb,
        'pagetype':pagetype,
        'imgheight':imgheight,
        'article_id':article_id},
        context_instance=RequestContext(request))

@csrf_exempt
@require_POST
@login_required
def imageUpload(request):
    try:
        article_id = request.GET['article']
    except:
        article_id = None

    for f in request.FILES.getlist("file"):
        obj = ArticleImage.objects.create(image=f)
        obj.uploaded_by = request.user
        obj.save()
        if obj.image.width > 1600:
            obj.image  = resizeImage(obj.image.path, 1600, 0)
            obj.save()
        header = ArticleImageCrop.objects.create(src = obj, type=(ArticleImageType.objects.get(name='header')))
        featured = ArticleImageCrop.objects.create(src = obj, type=(ArticleImageType.objects.get(name='featured')))
        thumb = ArticleImageCrop.objects.create(src = obj, type=(ArticleImageType.objects.get(name='thumbnail')))

        if article_id:
            article = get_object_or_404(Article, id=article_id)
            connectCrops(article.id,obj.id)
            return HttpResponseRedirect('/staff/image/'+str(obj.id)+'/?article='+str(article_id))
        return HttpResponseRedirect('/staff/image/'+str(obj.id))

@csrf_exempt
@require_POST
@login_required
def fileUpload(request):
    files = []
    for f in request.FILES.getlist("file"):
        obj = ContentImage.objects.create(image=f)
        obj.folder = 'Article Uploads'
        obj.save()
        files.append({"filelink": obj.cdn_url})
        logger.info(json.dumps(files))
    return HttpResponse(json.dumps(files), mimetype="application/json")

@csrf_exempt
@require_POST
@login_required
def fileUpdate(request):
    status = []
    file = ContentImage.objects.get(pk=request.POST['id'])
    file.title = request.POST['title']
    file.folder = request.POST['folder']
    file.save()
    status.append({'status':'saved'})
    return HttpResponse(json.dumps(status), mimetype="application/json")


@login_required
def recentFiles(request):
    files = [
        {"thumb": obj.cdn_url, "image": obj.cdn_url, "folder": obj.folder}
        for obj in ContentImage.objects.all().order_by("-uploaded")[:20]
        ]
    return HttpResponse(json.dumps(files), mimetype="application/json")    
        
@login_required
def staffHome(request):
    user = request.user
    posted = Article.objects.filter(is_posted=True).order_by("-date_posted")
    unposted = Article.objects.filter(is_posted=False).order_by("-date_posted")
    paginator = Paginator(posted, 30)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: posted = paginator.page(page)
    except (InvalidPage, EmptyPage):
        posted = paginator.page(paginator.num_pages)

    d = dict(posted=posted, unposted=unposted, user=user)
    return render_to_response("staffHome.html", d)

@login_required
def imagePicker(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    imagelist = ArticleImageCrop.objects.filter(type=(ArticleImageType.objects.get(name='header')), URL__isnull=False)

    paginator = Paginator(imagelist, 8)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: imagelist = paginator.page(page)
    except (InvalidPage, EmptyPage):
        imagelist = paginator.page(paginator.num_pages)

    if request.method == "POST":
            image = ArticleImage.objects.get(pk=request.POST['image'])
            connectCrops(article_id,image.id)
            return HttpResponseRedirect('/editor/'+str(article_id))

    d = dict(imagelist=imagelist, article=article)
    return render_to_response("imagePicker.html", d, context_instance=RequestContext(request))

@login_required
def staffFileManager(request):
    filelist = ContentImage.objects.all()

    d = dict(filelist=filelist)
    return render_to_response("staffFileManager.html", d)

@login_required    
def profilePage(request):
    user = request.user
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    notice = None
    
    if request.method == "POST":
        uform = UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and uform.is_valid():
            uform.save()
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            notice = "Saved!"
    
    else:
        form = ProfileForm(instance=profile)
        uform = UserForm(instance=request.user)
        
    return render_to_response("staffProfile.html", {
        'form': form,
        'uform': uform,
        'notice': notice,
        'user': user},
        context_instance=RequestContext(request))

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')