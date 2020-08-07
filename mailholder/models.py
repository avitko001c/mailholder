import os
import datetime
from tortoise import Tortoise
from tortoise.models import Model
from tortoise.fields import BinaryField, CharField, TextField, DateTimeField, JSONField, IntField, ManyToManyRelation, ManyToManyField
from configmanager import PlainConfig
##

#mailholder': f'mysql://{user}:"{passwd}"@{host}:{port}/{db}'},

tortoise_config = {
    'connections': {
	    'mailholder': {
        'engine': 'tortoise.backends.mysql',
        'credentials': {
            'host': os.environ.get('DATABASE_HOST', 'localhost'),
            'port': os.environ.get('DATABASE_PORT', '3308'),
            'user': os.environ.get('MYSQL_USERNAME', 'mailholder'),
            'passwd': os.environ.get('MYSQL_PASSWORD', 'Ma!lh0ld3r'),
            'database': os.environ.get('DATABASE', 'mailholder'),
        }
      }
    },
	'apps': {
       'models': {
           'models': ['mailholder.models', 'aerich.models'],
	       'default_connection': 'mailholder',
       }
    }
}
##

class BaseModel(Model):
    def __str__(self):
        return f"{self.__class__.__name__} {self.id}: {self.username}"

class Email(BaseModel):

    id = IntField(pk=True)
    from_email = CharField(255)
    to_email = TextField()
    bcc = TextField()
    cc = TextField()
    subject = CharField(255)
    context = TextField(null=True)
    created = DateTimeField(index=True, auto_now_add=True)
    headers = JSONField(null=False)
    html_message = TextField(null=True)
    last_updated = DateTimeField(index=True, default=datetime.datetime.now())
    message = TextField()
    file = BinaryField(null=True)
    filename = CharField(255, null=True)
    mimetype = CharField(255, null=True)
    emails =
    priority = IntField(null=True)
    scheduled_time = DateTimeField(index=True, null=True)
    status = IntField(index=True, null=True)

    class Meta:
        table = 'data_email'

class Log(BaseModel):
	email_id: ManyToManyRelation['Email'] = ManyToManyField("models.Email")
    date = DateTimeField(index=True, default=datetime.datetime.now())
    exception_type = CharField(null=True)
    message = TextField()
    status = IntField(index=True, null=True)

    class Meta:
        table = 'data_log'
