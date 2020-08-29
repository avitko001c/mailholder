from mongoengine import *
import datetime
connect('mailholder', host='mailholder.xy1qw.mongodb.net', username='mailholder', password='Test07!@')

class Attachment(Document):
    id = UUIDField()
    filename = StringField(required=True)
    file = FileField()

class Email(Document):
    recieved = DateTimeField(default=datetime.datetime.now())
    created = DateTimeField()
    from_address = EmailField(primary_key=True, required=True, allow_ip_domain=True)
    to_address = ListField(EmailField(required=True, allow_ip_domain=True), default=list)
    bcc = ListField(EmailField(), default=list)
    cc = ListField(EmailField(), default=list)
    subject = StringField()
    context = StringField()
    headers = ListField(tuple(), default=list)
    message = StringField()
    attachments = ListField(ReferenceField(Attachment, reverse_delete_rule=CASCADE), required=False)


