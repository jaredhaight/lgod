from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.utils.html import linebreaks
from app.models import Article
from main.settings import BASE_URL

class lgodFeed(Feed):
    title = "Live Geek or Die"
    link = BASE_URL
    description = "A site for New England geeks and gamers."

    def items(self):
        articles = Article.objects.filter(is_posted=True).order_by("-date_posted")
        list = articles.filter(Q(type='standard')|Q(type='featured'))[:10]
        return list

    def item_title(self,item):
        return item.title

    def item_author_name(self,item):
        try:
            author =  item.author.staffprofile.displayName
        except:
            author = item.author.username
        return author

    def item_author_link(self, item):
        username = item.author.username
        return BASE_URL+'/author/'+username.lower()

    def item_description(self, item):
        try:
            image = item.image.thumbnail.URL
        except:
            image = ''
        return '<img src='+image+'><p>'+item.body+'</p>'
