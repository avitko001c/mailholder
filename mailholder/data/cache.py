from django.template.defaultfilters import slugify

from .utils import get_cache_backend

# Stripped down version of caching functions from django-dbtemplates
# https://github.com/jezdez/django-dbtemplates/blob/develop/dbtemplates/utils/cache.py

class Cache:
    def __init__(self, name):
        self.cache_backend = get_cache_backend()
        self.name = name

    def get_cache_key(self):
        """
        Prefixes and slugify the key name
        """
        return 'post_office:template:%s' % (slugify(self.name))


    def set(self, content):
        return self.cache_backend.set(self.get_cache_key(self.name), content)


    def get(self):
        return self.cache_backend.get(self.get_cache_key(self.name))


    def delete(self):
        return self.cache_backend.delete(self.get_cache_key(self.name))
