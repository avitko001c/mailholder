import os
import datetime
from peewee import *
from playhouse.mysql_ext import JSONField, MySQLConnectorDatabase

config ={
    'charset': 'utf8',
    'sql_mode': 'PIPES_AS_CONCAT',
    'use_unicode': True,
    'user': os.environ.get('MYSQL_USERNAME', 'root'),
    'passwd': os.environ.get('MYSQL_PASSWORD', 'Julia07!@'),
    'database': 'mailholder'
}

database = MySQLDatabase(**config)

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class DataAttachment(BaseModel):
    file = BigBitField()
    filename = CharField()
    mimetype = CharField()

    class Meta:
        table_name = 'data_attachment'

class DataUser(BaseModel):
    username = CharField(unique=True)
    email_address = CharField()

    class Meta:
        table_name = 'data_user'

class DataEmail(BaseModel):
    username = ForeignKeyField(column_name='username_id', field='id', model=DataUser)
    to = TextField()
    bcc = TextField()
    cc = TextField()
    subject = CharField()
    context = TextField(null=True)
    created = DateTimeField(index=True)
    from_email = CharField()
    headers = JSONField(null=False)
    html_message = TextField(null=True)
    last_updated = DateTimeField(index=True, default=datetime.datetime.now())
    message = TextField()
    attachment = ForeignKeyField(column_name='attachment_id', field='id', model=DataAttachment, null=True)
    priority = IntegerField(null=True)
    scheduled_time = DateTimeField(index=True, null=True)
    status = IntegerField(index=True, null=True)

    class Meta:
        table_name = 'data_email'

class DataLog(BaseModel):
    date = DateTimeField(index=True, default=datetime.datetime.now())
    email = ForeignKeyField(column_name='email_id', field='id', model=DataEmail)
    username = ForeignKeyField(column_name='username_id', field='id', model=DataUser)
    exception_type = CharField(null=True)
    message = TextField()
    status = IntegerField(index=True, null=True)

    class Meta:
        table_name = 'data_log'
