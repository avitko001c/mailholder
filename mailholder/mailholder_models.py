from peewee import *
from playhouse.mysql_ext import JSONField

database = MySQLDatabase('mailholder', **{'charset': 'utf8', 'sql_mode': 'PIPES_AS_CONCAT', 'use_unicode': True, 'user': 'root', 'passwd': 'Julia07!@'})

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

class DataEmailtemplate(BaseModel):
    content = TextField()
    created = DateTimeField()
    default_template = ForeignKeyField(column_name='default_template_id', field='id', model='self', null=True)
    description = TextField()
    html_content = TextField()
    language = CharField()
    last_updated = DateTimeField()
    name = CharField()
    subject = CharField()

    class Meta:
        table_name = 'data_emailtemplate'
        indexes = (
            (('name', 'language', 'default_template'), True),
        )

class DataUser(BaseModel):
    email_address = CharField()
    name = CharField()

    class Meta:
        table_name = 'data_user'

class DataEmail(BaseModel):
    to = TextField()
    bcc = TextField()
    cc = TextField()
    subject = CharField()
    context = TextField(null=True)
    created = DateTimeField(index=True)
    from_email = CharField()
    headers = JSONField(null=False)
    html_message = TextField()
    last_updated = DateTimeField(index=True)
    message = TextField()
    priority = IntegerField(null=True)
    scheduled_time = DateTimeField(index=True, null=True)
    status = IntegerField(index=True, null=True)
    template = ForeignKeyField(column_name='template_id', field='id', model=DataEmailtemplate, null=True)
    username = ForeignKeyField(column_name='username_id', field='id', model=DataUser, null=True)

    class Meta:
        table_name = 'data_email'

class DataAttachmentEmails(BaseModel):
    attachment = ForeignKeyField(column_name='attachment_id', field='id', model=DataAttachment)
    email = ForeignKeyField(column_name='email_id', field='id', model=DataEmail)

    class Meta:
        table_name = 'data_attachment_emails'
        indexes = (
            (('attachment', 'email'), True),
        )

class DataLog(BaseModel):
    date = DateTimeField()
    email = ForeignKeyField(column_name='email_id', field='id', model=DataEmail)
    exception_type = CharField()
    message = TextField()
    status = IntegerField()

    class Meta:
        table_name = 'data_log'

class DjangoMigrations(BaseModel):
    app = CharField()
    applied = DateTimeField()
    name = CharField()

    class Meta:
        table_name = 'django_migrations'

