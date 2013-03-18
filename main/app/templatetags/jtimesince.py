__author__ = 'jared'
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def age(value):
    return '%(time)s' % {'time': timesince(value).split(', ')[0]}