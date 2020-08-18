from pony.orm import *
from uuid import uuid4

db = Database()

class Attachment(db.Entity):
    file = Optional(bytes)
