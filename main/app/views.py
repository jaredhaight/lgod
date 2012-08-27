# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import datetime
import json
import logging
from app.models import *

logger = logging.getLogger(__name__)


def home(request):
    articles = get_list_or_404(Article.objects.filter(is_posted=True).order_by("-date_posted"))
    paginator = Paginator(articles, 10)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles)
    return render_to_response("home.html", d)

def category(request, jslug):
    articles = get_list_or_404(Article.objects.filter(categories__name=jslug, is_posted=True).order_by("-date_posted"))
    paginator = Paginator(articles, 10)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles)
    return render_to_response("home.html", d)
    
def article(request, jslug):
    user = request.user
    posted = None
    
    if request.user.is_authenticated():
        article = get_object_or_404(Article, title_slug=str(jslug))
    else:
        article = get_object_or_404(Article, title_slug=str(jslug), is_posted=True)
    
    if article.is_posted == True:
        posted = 'posted'
    
    d = dict(user=user,article=article, posted=posted)
    return render_to_response("article.html", d)

@login_required
def newArticle(request):
    posted = None
    article = None
    
    if request.method == 'POST':
        if "discard_article" in request.POST:
            return HttpResponseRedirect('/staff')
        else:
            form = ArticleForm(request.POST, instance=article)
            if form.is_valid():
                article = form.save(commit=False)
                if "post_article" in request.POST:
                    now = datetime.datetime.now()
                    article.date_posted = now.strftime("%Y-%m-%dT%H:%M:%S")
                    article.is_posted = True
                elif "unpost_article" in request.POST:
                    article.is_posted = False
                article.author = request.user.first_name
                article.title_slug = slugify(article.title)
                article.save()
                return HttpResponseRedirect('/article/'+article.title_slug)  
                
    elif article != None:
        form = ArticleForm(instance=article)
        if article.is_posted == True:
            posted = 'posted'
    else:
        form = ArticleForm()
        
    return render_to_response("editor.html", {
        'form': form},
        context_instance=RequestContext(request))
        
@login_required
def articleEditor(request, jslug):
    posted = None
    article = get_object_or_404(Article, title_slug=str(jslug))

    if request.method == 'POST':
        if "discard_article" in request.POST:
            return HttpResponseRedirect('/staff')
        else:
            form = ArticleForm(request.POST, instance=article)
            if form.is_valid():
                article = form.save(commit=False)
                if "post_article" in request.POST:
                    now = datetime.datetime.now()
                    article.date_posted = now.strftime("%Y-%m-%dT%H:%M:%S")
                    article.is_posted = True
                    article.author = request.user.first_name                    
                elif "unpost_article" in request.POST:
                    article.is_posted = False
                article.title_slug = slugify(article.title)
                article.save()
                form.save_m2m()
                return HttpResponseRedirect('/article/'+article.title_slug)
            
    else:
        form = ArticleForm(instance=article)
        if article.is_posted == True:
            posted = 'posted'
            
    return render_to_response("editor.html", {
        'form': form,
        'article' : article,
        'posted' : posted},
        context_instance=RequestContext(request))

@csrf_exempt
@require_POST
@login_required
def fileUpload(request):
    files = []
    for f in request.FILES.getlist("file"):
        obj = FileUpload.objects.create(file=f)
        obj.save()
        files.append({"filelink": obj.cdn_url})
        logger.info(json.dumps(files))
    return HttpResponse(json.dumps(files), mimetype="application/json")

@login_required
def recentFiles(request):
    files = [
        {"thumb": obj.file.url, "image": obj.cdn_url}
        for obj in FileUpload.objects.all().order_by("-uploaded")[:20]
        ]
    return HttpResponse(json.dumps(files), mimetype="application/json")    
        
@login_required
def staffHome(request):
    user = request.user
    articles = get_list_or_404(Article.objects.all().order_by("-date_posted"))
    paginator = Paginator(articles, 30)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, user=user)
    return render_to_response("staffHome.html", d)

@login_required    
def profilePage(request):
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
    
    else:
        form = ProfileForm(instance=profile)
        
    return render_to_response("profile.html", {
        'form': form},
        context_instance=RequestContext(request))