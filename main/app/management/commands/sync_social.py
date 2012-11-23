__author__ = 'jared'
from django.core.management.base import BaseCommand
from app.models import Article
from app.social import update_social_stats
from datetime import datetime, timedelta
from main.settings import LOGGING_DIR

import logging
logger = logging.getLogger('lgod')
hdlr = logging.FileHandler(LOGGING_DIR+'social_sync.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class Command(BaseCommand):
    def handle(self, *args, **options):
        articles = Article.objects.filter(is_posted=True, date_posted__gte=datetime.now()-timedelta(days=30))
        for article in articles:
            update_social_stats(article)
            logger.info('Updated article: "%s"'% article.title)
