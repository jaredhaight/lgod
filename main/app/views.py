# Create your views here.
from django.db.models import Q
from django.contrib.auth import logout
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_change, password_change_done
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponsePermanentRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import feedparser
from time import mktime
from datetime import datetime, timedelta



from app.models import *

logger = logging.getLogger(__name__)

def set_cookie(response, key, value, days_expire = 7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  #one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires)


def article_edit_rights(user, article):
    #determines if a user has rights to edit an article
    if user.groups.filter(name='editors').count() > 0:
        return True
    if article.author == user:
        return True
    return False

def latestComments():
    url = 'http://lgod.disqus.com/latest.rss'
    comments = feedparser.parse(url)
    count = 0
    results = []
    now = datetime.now()
    for item in comments['items'][:6]:
        title = item['title_detail']['value']
        comment = item['summary_detail']['value']
        author = item['author_detail']['name']
        link = item['link']
        posted = datetime.fromtimestamp(mktime(item['updated_parsed']))
        difference = now - posted
        print title +' '+ str(difference) + ' ' + str(posted) + ' ' + str(now)
        if difference.days > 0:
            clean_time = str(difference.days)+' day(s) ago'
        elif difference.seconds > 3600:
            clean_time = str((difference.seconds /60) / 60) + ' hours ago'
        elif difference.seconds > 60:
            clean_time = str(difference.seconds /60) + ' minutes ago'
        else:
            clean_time = str(difference.seconds) + ' seconds ago'
        result = {'title':title.replace('Re: ','').replace(' - Live Geek or Die',''),'comment':comment,'time':clean_time,'author':author, 'link':link}
        results.append(result)
    return results

def urlRedirect(request, subcat, oldid):
    if not oldid:
        return HttpResponsePermanentRedirect('/category/'+subcat)
    else:
        print('URLRedirect got '+oldid)
        newid = get_object_or_404(URLRedirect, oldid=oldid)
        article = get_object_or_404(Article, id=newid.newid)
        return HttpResponsePermanentRedirect('/article/'+article.title_slug)

def legacyArticleImageRedirect(request, imageString, article_id):
    print imageString
    return HttpResponsePermanentRedirect('/media/lgod_old/'+imageString)


def home(request):
    user = request.user
    articles = Article.objects.filter(is_posted=True).order_by("-list_date")

    features = articles.filter(type='featured')[:3]
    articlelist= articles.filter(type='standard')[:18]
    sidebarlist = articles.filter(type='sidebar')[:12]
    row1 = articlelist[:6]
    row2 = articlelist[6:12]
    row3 = articlelist[12:18]
    notespage1 = sidebarlist[:4]
    notespage2 = sidebarlist[4:8]
    notespage3 = sidebarlist[8:12]
    d = dict(features=features, articlelist=articlelist, row1=row1, row2=row2, row3=row3, user=user, notespage1=notespage1, notespage2=notespage2, notespage3=notespage3)
    return render_to_response("home.html", d, context_instance=RequestContext(request))

def archive(request):
    user = request.user
    articles = Article.objects.filter(is_posted=True).order_by("-list_date")
    paginator = Paginator(articles, 18)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles)
    return render_to_response("archive.html", d, context_instance=RequestContext(request))

def category(request, jslug):
    user = request.user
    articles = Article.objects.filter(categories__slug=jslug, is_posted=True).order_by("-list_date")
    paginator = Paginator(articles, 18)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, user=user)
    return render_to_response("archive.html", d, context_instance=RequestContext(request))
    
def authorPage(request, jslug):
    social = None
    user = request.user
    staff = get_object_or_404(User, username__iexact=str(jslug))
    articles = get_list_or_404(Article.objects.filter(author__username=jslug, is_posted=True).order_by("-list_date"))
    
    try: staffProfile = StaffProfile.objects.get(user=User.objects.get(username=jslug))
    except: staffProfile = None
    
    if staffProfile.twitter or staffProfile.facebook or staffProfile.gplus:
        social = 'social'

    paginator = Paginator(articles, 14)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, staff=staff, staffProfile=staffProfile, social=social, user=user)
    return render_to_response("authorPage.html", d, context_instance=RequestContext(request))
    
def article(request, article_id, type):
    user = request.user
    posted = None
    updated = None
    pagetype = 'article'

    if type=='editorPreview' and request.user.is_authenticated():
        article = get_object_or_404(Article, id=article_id)
    else:
        article = get_object_or_404(Article, title_slug=str(article_id), is_posted=True)

    editable = article_edit_rights(user,article)

    if article.is_posted:
        posted = 'posted'

    if article.date_posted != article.list_date:
        updated = article.list_date

    d = dict(user=user,article=article, posted=posted, pagetype=pagetype, editable=editable, updated=updated)
    return render_to_response("articleView.html", d, context_instance=RequestContext(request))

@csrf_exempt
@login_required
def articleEditor(request, article_id):
    user = request.user
    posted = None
    errors = None
    status = "new"
    if article_id:
        article = get_object_or_404(Article, pk=article_id)
        if not article_edit_rights(user, article):
            return HttpResponseForbidden()
        status, errors = article.post_status()

    else:
        article = None

    try: staffProfile = StaffProfile.objects.get(user=user)
    except: staffProfile = None

    if not staffProfile:
        return HttpResponseRedirect('/staff/profile/?src=article')


    if request.method == 'POST':
        if "discard_article" in request.POST:
            return HttpResponseRedirect('/staff')
        else:
            try: article = Article.objects.get(pk=article_id)
            except:
                article = None
            form = ArticleForm(request.POST, request.FILES, instance=article)
            print str(form)
            if form.is_valid():
                article = form.save(commit=False)
                if "post_article" in request.POST:
                    status = article.post_status()
                    if status[0] == 'ready_to_post':
                        now = datetime.now()
                        article.date_posted = now.strftime("%Y-%m-%dT%H:%M:%S")
                        article.list_date = article.date_posted
                        article.title_slug = uniqueSlug('Article', article.id, 'title_slug', article.title)
                        article.is_posted = True
                    else:
                        errors.append("Article post status is not 'ready_to_post'. Can not post this article.")
                        return render_to_response("articleEditor.html", {
                            'form': form,
                            'article' : article,
                            'posted' : posted,
                            'user' : user,
                            'status':status,
                            'errors':errors},
                            context_instance=RequestContext(request))
                elif "republish_article" in request.POST:
                    now = datetime.now()
                    article.list_date = now.strftime("%Y-%m-%dT%H:%M:%S")
                elif "unpost_article" in request.POST:
                    article.is_posted = False
                if not article.author:
                    article.author = request.user
                article.edit_user = request.user
                article.save()
                form.save_m2m()
                if "pick_photo" in request.POST:
                    return HttpResponseRedirect('/editor/'+str(article.id)+'/picker')
                if "new_photo" in request.POST:
                    return HttpResponseRedirect('/staff/image/upload/?article='+str(article.id))
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
        'status':status},
        context_instance=RequestContext(request))

@csrf_exempt
@require_POST
@login_required
def articleAutosave(request, article_id):
    status = []
    article = Article.objects.get(pk=article_id)
    try:
        data = json.loads(request.body)
    except:
        data = None

    try:
        title = data['title']
    except:
        title = None

    try:
        body = data['body']
    except:
        body = None

    try:
        summary = data['summary']
    except:
        summary = None

    try:
        type = data['type']
    except:
        type = None

    try:
        categories = data['categories']
    except:
        categories = None
    if title:
        article.title = title
        status.append({'title':'saved'})
    if body:
        article.body = body
        status.append({'body':'saved'})
    if summary:
        article.summary = summary
        status.append({'summary':'saved'})
    if categories:
        article.categories = categories
        status.append({'categories':'saved'})
    if type:
        article.type = type
        status.append({'type':'saved'})
    print status
    article.save()
    return HttpResponse(json.dumps(status), mimetype="application/json")

@login_required
def imageEditor(request,image_id):
    articleImage = get_object_or_404(ArticleImage, id=image_id)
    headerType = ArticleImageType.objects.get(name='header')
    thumbnailType = ArticleImageType.objects.get(name='thumbnail')
    header = ArticleImageCrop.objects.get(type=headerType.id, src=articleImage.id)
    thumbnail = ArticleImageCrop.objects.get(type=thumbnailType.id, src=articleImage.id)
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
        'headerType': headerType,
        'thumbnailType': thumbnailType,
        'header':header,
        'thumbnail':thumbnail,
        'imgheight':imgheight,
        'article_id':article_id},
        context_instance=RequestContext(request))

@login_required
def imageUpload(request):
    try:
        article_id = request.GET['article']
    except:
        article_id = None

    if request.method == "POST":
        try:
            article_id = request.GET['article']
        except:
            article_id = None
        form = ArticleImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.uploaded_by = request.user
            image.save()
            header = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='header')))
            mediumHeader = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='mediumHeader')))
            smallHeader = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='smallHeader')))
            thumb = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='thumbnail')))
            smallFeatured = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='smallFeatured')))
            mediumFeatured = ArticleImageCrop.objects.create(src = image, type=(ArticleImageType.objects.get(name='mediumFeatured')))
            if article_id:
                article = get_object_or_404(Article, id=article_id)
                article.image = image
                article.save()
                return HttpResponseRedirect('/staff/image/'+str(image.id)+'/?article='+str(article_id))
            return HttpResponseRedirect('/staff/image/'+str(image.id))
    else:
        form = ArticleImageForm()

    return render_to_response("imageUpload.html", {
        'form': form,
        'article_id':article_id},
        context_instance=RequestContext(request))

@login_required
def imagePicker(request, article_id):

    article = get_object_or_404(Article, id=article_id)
    imagelist = ArticleImageCrop.objects.filter(type=(ArticleImageType.objects.get(name='thumbnail')), URL__isnull=False).order_by("-id")

    paginator = Paginator(imagelist, 16)

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
    if user.groups.filter(name='editors').count() > 0:
        editor = True
        posted = Article.objects.filter(is_posted=True).order_by("-list_date")
        unposted = Article.objects.filter(is_posted=False).order_by("-list_date")
    else:
        editor = False
        posted = Article.objects.filter(is_posted=True, author=user).order_by("-list_date")
        unposted = Article.objects.filter(is_posted=False, author=user).order_by("-list_date")

    paginator = Paginator(posted, 10)
    draftcount = len(unposted)
    comments = latestComments()
    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: posted = paginator.page(page)
    except (InvalidPage, EmptyPage):
        posted = paginator.page(paginator.num_pages)

    d = dict(posted=posted, unposted=unposted, user=user, editor=editor, draftcount = draftcount, comments=comments)
    return render_to_response("staffHome.html", d, context_instance=RequestContext(request))

@login_required()
def staffDrafts(request):
    user = request.user
    if user.groups.filter(name='editors').count() > 0:
        editor = True
        unposted = Article.objects.filter(is_posted=False).order_by("-list_date")
    else:
        editor = False
        unposted = Article.objects.filter(is_posted=False, author=user).order_by("-list_date")

    paginator = Paginator(unposted, 15)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: posted = paginator.page(page)
    except (InvalidPage, EmptyPage):
        posted = paginator.page(paginator.num_pages)

    d = dict(unposted=unposted, user=user, editor=editor)
    return render_to_response("staffDrafts.html", d, context_instance=RequestContext(request))

@login_required
def staffImages(request):
    user = request.user
    if user.groups.filter(name='editors').count() == 0:
        return HttpResponseForbidden()
    else:
        imagelist = ArticleImageCrop.objects.filter(type=(ArticleImageType.objects.get(name='thumbnail')), URL__isnull=False).order_by("-id")
        paginator = Paginator(imagelist, 16)

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
        return render_to_response("imageList.html", d, context_instance=RequestContext(request))

@login_required    
def profilePage(request):
    user = request.user
    print 'User first name at load: '+request.user.first_name
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    notice = None

    try:
        source = request.GET['src']
    except:
        source = None
    
    if request.method == "POST":
        firstName = user.first_name
        uform = UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and uform.is_valid():
            userForm = uform.save(commit=False)
            userForm.first_name = firstName
            userForm.save()
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
        'user': user,
        'source':source},
        context_instance=RequestContext(request))

def about(request):
    return render_to_response("about.html", context_instance=RequestContext(request))

def change_password(request,template_name="staffPassword.html"):
    return password_change(request,template_name=template_name, post_change_redirect=reverse('app.views.password_change_done'))

@login_required
def password_change_done(request, template_name="staffPasswordDone.html"):
    return render_to_response(template_name,(),context_instance= RequestContext(request))

def login_view(request):
    username = password = ''
    state = 'Please enter your username and password'
    if request.GET.get('next'):
        next = request.GET.get('next')
    else:
        next = '/'

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                response = HttpResponseRedirect(next)
                set_cookie(response, 'PassCache', 'True', days_expire=None)
                return response
        else:
            state = "Your username and/or password were incorrect."

    if request.user.is_authenticated():
        response = HttpResponseRedirect(next)
        set_cookie(response, 'PassCache', 'True', days_expire=None)
        return response

    return render_to_response('login.html',{'state':state, 'next':next}, context_instance=RequestContext(request))

def logout_view(request):
    logout(request)
    response = HttpResponseRedirect('/')
    set_cookie(response, 'PassCache', 'False', days_expire=None)
    return response

def fourohfour(request):
    return render_to_response('404.html')

def fourohthree(request):
    return render_to_response('403.html')
