import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# example) SQLite
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}

POST_OFFICE = {
    'DEFAULT_PRIORITY' : 'now'
}

# example) MySQL
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.mysql',
         'NAME': 'mailholder',
         'USER': 'root',
         'PASSWORD': 'Julia07!@',
         'HOST': 'localhost',
         'PORT': '3306',
     }
 }

INSTALLED_APPS = (
    'data',
    'localserver',
)

SECRET_KEY = 'b@mv-i+2kx79wum5syyvzej8)7qpi-=ne%k!2d)q(i9@6i%_7e'
