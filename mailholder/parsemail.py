import os, re, sys, django, email
from io import BytesIO
from itertools import count
from smtpd import SMTPServer
from aiosmtpd.controller import Controller
from playhouse.dataset import DataSet

db = DataSet('sqlite:///memory:')
sys.dont_write_bytecode = True
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

VERSION = "1.3.1"
ERROR_NOUSER = 67
ERROR_PERM_DENIED = 77
ERROR_TEMP_FAIL = 75
UID_GENERATOR = count()
LAST_UID = next(UID_GENERATOR)

def get_counter():
    global LAST_UID
    LAST_UID = next(UID_GENERATOR)
    return LAST_UID

# regular expresion from https://github.com/django/django/blob/master/django/core/validators.py
email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    # quoted-string, see also http://tools.ietf.org/html/rfc2822#section-3.2.5
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'
    r')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)'  # domain
    r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE)

email_extract_re = re.compile("<(([.0-9a-z_+-=]+)@(([0-9a-z-]+\.)+[0-9a-z]{2,9}))>", re.M|re.S|re.I)
filename_re = re.compile("filename=\"(.+)\"|filename=([^;\n\r\"\']+)", re.I|re.S)

begin_tab_re = re.compile("^\t{1,}", re.M)
begin_space_re = re.compile("^\s{1,}", re.M)

class MessagePart(object):

    def __init__(self, msg):
        self.msg = email.message_from_bytes(msg)
        self.string_file = BytesIO()

    def to_json(self):
        import json
        out = {}
        for header in self.msg.keys():
            out[header] = self.msg.get(header, '')
        if self.msg.is_multipart:
            num = 0
            out['Content'] = {}
            for payload in self.msg.get_payload():
                out['Content']['MultiPart' + str(num)] = {}
                for key in payload.keys():
                    out['Content']['MultiPart' + str(num)][key] = payload.get(key, '')
                if isinstance(payload._payload, list):
                    for x in payload._payload:
                        out['Content']['MultiPart' + str(num)]['Content'] = x.as_string()
                    num += 1
                    continue
                out['Content']['MultiPart' + str(num)]['Content'] = payload._payload
                num += 1
            return out
        else:
            out['Content'] = self.msg._payload
            print(type(out))
            out = BytesIO(str(out).encode())
            return json.loads(out)

    def saveHeaders(self):
        headers = db['headers']
        for header in self.msg.keys():
            headers.insert(self.msg.get(header, ''))
        return headers

    def saveAttachments(self, path):
        if not os.path.exists(path):
            raise NotADirectoryError('Path {0} does not exist'.format(path))
        outfiles = []
        for part in self.msg.walk():
            if part.is_multipart():
                continue
            if part.get_content_disposition() is None:
                continue
            fileName = part.get_filename()
            outfile = BytesIO()
            if bool(fileName):
                filePath = os.path.join(str(path), str(fileName))
                if not os.path.isfile(filePath):
                    fp = open(filePath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                subject = self.msg.get('Subject', '')
                print('Downloaded {0} from email with Subject: {1} into {2}'.format(fileName, subject, path))
                outfile.write(part.get_payload(decode=True))
        return outfiles


    def getBodyFile(self, decode=False):
        if self.msg.is_multipart():
            self.string_file.seek(0)
            for part in self.msg.walk():
                if part.is_multipart():
                    continue
                if part.get('Content-Disposition') is not None:
                    continue
                payload = part._payload
                if not isinstance(payload, bytes):
                    payload = payload.encode('ascii', 'surrogateescape')
                self.string_file.write(payload)
            self.string_file.seek(0)
            return self.string_file
        # On Python 3, the payload may be a string created using
        # surrogate-escape encoding.
        # We can't get at this through the public API, without also undoing
        # any Content-Transfer-Encoding, which would be tedious to recreate
        # so we access the private field. This may cause issues in future.
        # ¯\_(ツ)_/¯
        self.string_file.seek(0)
        payload = self.msg._payload
        if not isinstance(payload, bytes):
            payload = payload.encode('ascii', 'surrogateescape')
        self.string_file.write(payload)
        self.string_file.seek(0)
        return self.string_file

    def getSize(self):
        return len(self.msg.as_string())

    def isMultipart(self):
        return self.msg.is_multipart()

    def getSubPart(self, part):
        if self.msg.is_multipart():
            return MessagePart(self.msg.get_payload()[part])
        raise TypeError("Not a multipart message")

    def payloads(self):
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            payload = part.get_payload(decode=True)
            enc = self.parse_charset()
            try:
                yield payload.decode(enc)
            except UnicodeDecodeError:
                yield payload

    def parse_charset(self, default='utf8'):
        charset = self.msg.get_charset()
        if charset is not None:
            return charset

        for chunk in self.msg['Content-type'].split(';'):
            if 'charset' in chunk:
                return chunk.split('=')[1]
        return default

    def unicode(self, header):
        """Converts a header to unicode"""
        value = self.msg[header]
        parts = email.header.decode_header(value)
        return ''.join(
            decoded_part.decode(codec)
            if codec is not None else decoded_part.decode('ascii')
            for decoded_part, codec in parts)


class LocalMessage(MessagePart):

    def __init__(self, fp, flags, date):
        # email.message_from_binary_file is new in Python 3.3,
        # and we need to use it if we are on Python3.
        if hasattr(email, 'message_from_binary_file'):
            parsed_message = email.message_from_binary_file(fp)
        else:
            parsed_message = email.message_from_file(fp)
        super(LocalMessage, self).__init__(parsed_message)
        self.data = str(self.msg)
        self.uid = get_counter()
        self.flags = set(flags)
        self.date = date

    def getUID(self):
        return self.uid

    def getFlags(self):
        return self.flags

    def getInternalDate(self):
        return self.date

    def __repr__(self):
        h = self.saveHeaders()
        return "<From: %s, To: %s, Uid: %s>" % (h['From'], h['To'], self.uid)



class LocalServer(SMTPServer):

    def _print_message_headers(self, peer, data, msg):
        inheaders = 1
        lines = data.splitlines()
        print(msg.getHeaders())
        for line in lines:
            # headers first
            if inheaders and not line:
                peerheader = 'X-Peer: ' + peer[0]
                if not isinstance(data, str):
                    # decoded_data=false; make header match other binary output
                    peerheader = repr(peerheader.encode('utf-8'))
                print(peerheader)
                inheaders = 0
            if not isinstance(data, str):
                # Avoid spurious 'str on bytes instance' warning.
                line = repr(line)
            print(line)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print(type(data))
        #print(data)
        msg_data = BytesIO(data)
        flags = []
        date = email.utils.formatdate()
        msg = LocalMessage(msg_data, flags, date)
        msg.msg.add_header('X-peer:', peer[0])
        #print(mailfrom, rcpttos)
        #print('Downloading Attachment')
        msg.getAttachment('/tmp')
        print('---------- MESSAGE FOLLOWS ----------')
        if kwargs:
            if kwargs.get('mail_options'):
                print('mail options: %s' % kwargs['mail_options'])
            if kwargs.get('rcpt_options'):
                print('rcpt options: %s\n' % kwargs['rcpt_options'])
        #print(msg.getBodyFile().read())
        filename = filename_re.match
        #print(message.items())
        #print('------------ END MESSAGE ------------')

class LocalHandler:
    async def handle_DATA(self, server, session, envelope, **kwargs):
        print(type(envelope.content))
        #print(data)
        msg_data = BytesIO(envelope.content)
        flags = []
        date = email.utils.formatdate()
        msg = LocalMessage(msg_data, flags, date)
        #msg.msg.add_header('X-peer:', peer[0])
        print(msg.msg)
        #print(mailfrom, rcpttos)
        #print('Downloading Attachment')
        #msg.getAttachment('/tmp')
        print('---------- MESSAGE FOLLOWS ----------')
        if kwargs:
            if kwargs.get('mail_options'):
                print('mail options: %s' % kwargs['mail_options'])
            if kwargs.get('rcpt_options'):
                print('rcpt options: %s\n' % kwargs['rcpt_options'])
        #print(msg.getBodyFile().read())
        filename = filename_re.match
        #print(message.items())
        print('------------ END MESSAGE ------------')
        return '250 OK'

