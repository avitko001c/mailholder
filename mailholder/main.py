# Django specific settings
import os
import sys
import django
sys.dont_write_bytecode = True
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Ensure settings are read
# Django 1.x uses get_wsgi_application()
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()
# Django 2.x uses django.setup()
application = django.setup()

# Your application specific imports
from data.models import *


#Add user
user = User(name="masnun", email_address="masnun@gmail.com")
user.save()

# Application logic
first_user = User.objects.all()[0]

print(first_user.name)
print(first_user.email_address)
