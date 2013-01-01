import datetime
from haystack import indexes
from app.models import Article


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='author')
    date_posted = indexes.DateTimeField(model_attr='date_posted')

    def get_model(self):
        return Article

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return  self.get_model().objects.filter(is_posted=True).order_by("-date_posted").exclude(type='sidebar')

