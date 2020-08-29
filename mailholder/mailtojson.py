# ---------------------------------------------------------------------
#  (c) 2013 Newsman App, https://github.com/Newsman/MailToJson
#  (c) 2015 Mike Andersen, mike@geekpod.net
#  (c) 2015 Andriy Vitushynskyy, vitush.dev@gmail.com
#
#  This code is released under MIT license.
# ---------------------------------------------------------------------

import re
import sys
import datetime
import email
import base64
import chardet


# Python 2.7 compatibility.
if sys.version_info < (3,):
    from email import Header as email_header

else:
    from email import header as email_header

    def unicode(value, encoding='utf-8', errors='strict'):
        """Convert to unicode"""
        return str(value, encoding, errors)

###########################################################################

# Regular expression from
#  https://github.com/django/django/blob/master/django/core/validators.py

EMAIL_RE = re.compile(
    # dot-atom
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    # quoted-string, see also http://tools.ietf.org/html/rfc2822#section-3.2.5
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
    r'|\\[\001-\011\013\014\016-\177])*"'
    # domain part
    r')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
    r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)'
    r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
    r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE)

EMAIL_EXTRACT_RE = re.compile(
    r"(([.0-9a-z_+-=]+)@(([0-9a-z-]+\.?)+[0-9a-z]{2,9}))", re.M | re.S | re.I)
FILENAME_RE = re.compile(
    r"filename=\"(.+)\"|filename=([^;\n\r\"\']+)", re.I | re.S)

BEGIN_TAB_RE = re.compile(r"^\t+", re.M)
BEGIN_SPACE_RE = re.compile(r"^\s+", re.M)


def decode_value(header_value, encoding):
    """Decode header value"""
    encoding = encoding.lower() if encoding else "ascii"
    if chardet.detect(header_value)['encoding'] == encoding:
        # Do not encode second time.
        return header_value
    header_value = unicode(header_value, encoding).strip().strip("\t")
    return header_value.encode(encoding)


class MailJson(object):
    """Class to convert between json and mail format"""

    def __init__(self, data, encoding=None):
        self.encoding = encoding
        self.include_headers = ()
        self.rcpt_headers = ["from", "to", "cc", "bcc", 'reply-to']
        self.json_data = {}
        self.raw_parts = []

        if isinstance(data, email.message.Message):
            self.mail = data
            self.parse_mail()
        elif type(data) is dict:
            raise NotImplementedError('Conversion from JSON to mail is not Supported')
        else:
            raise TypeError('Unknown data-type passed - Must be email.message.Message')

    @staticmethod
    def _decode_headers(headers, encoding=None):
        """Decode headers"""
        if type(headers) is not list:
            headers = [headers]
        ret = []
        for header in headers:
            header = email_header.decode_header(header)
            h_ret = []
            for (value, h_encoding) in header:
                decoded_hv = decode_value(value, h_encoding)
                if encoding:
                    enc = chardet.detect(value)['encoding']
                    if not enc:
                        enc = 'ascii'
                    decoded_hv = decoded_hv.decode(enc).encode(encoding)

                h_ret.append(decoded_hv)
            if len(h_ret) == 1:
                h_ret = h_ret[0]
            ret.append(h_ret)
        return ret

    def _get_part_headers(self, part):
        """Get headers from message part"""
        # raw headers
        headers = {}
        include_headers = self.include_headers
        for h_key in part.keys():
            if include_headers and h_key.lower() not in include_headers:
                continue
            h_key = h_key.lower()
            h_value = part.get_all(h_key)
            if isinstance(h_value, bytes):
                h_value = self._decode_headers(h_value, self.encoding)
            headers[h_key] = h_value[0] if len(h_value) == 1 else h_value
        return headers

    @staticmethod
    def _parse_date(data):
        """Parse date"""
        import calendar
        if data is None:
            return email.utils.format_datetime(datetime.datetime.now())
        if type(data) is list:
            data = str(data[0])
        time_tuple = datetime.datetime.timetuple(email.utils.parsedate_to_datetime(data))
        year, month, day, hour, minute, second, week_day, year_day, isdst = time_tuple
        return {'year': year,
                'month': calendar.month_name[month],
                'day': calendar.day_name[week_day],
                'hour': hour,
                'minute': minute,
                'second': second, }

    @staticmethod
    def _fix_encoded_subject(subject):
        """Convert encoded multi-line subject to one line"""
        if subject is None:
            return ""
        subject = "%s" % subject
        subject = subject.strip()

        if len(subject) < 2:
            # empty string or not encoded string ?
            return subject
        if subject.find("\n") == -1:
            # is on single line
            return subject
        if subject[0:2] != "=?":
            # not encoded
            return subject

        subject = subject.replace("\r", "")
        subject = BEGIN_TAB_RE.sub("", subject)
        subject = BEGIN_SPACE_RE.sub("", subject)
        lines = subject.split("\n")

        new_subject = ""
        for line in lines:
            new_subject = "%s%s" % (new_subject, line)
            if line[-1] == "=":
                new_subject = "%s\n " % new_subject
        return new_subject

    def _get_recipient_list(self, header):
        """Get list of recipients from header by name"""
        rcpts = self.mail.get_all(header, None)
        if not rcpts:
            return None
        if isinstance(rcpts, list):
            rcpts = ",".join(rcpts)
        # Get list of recipients
        rcpts = rcpts.replace("\n", " ").replace("\r", " ").strip()
        return rcpts.split(',')

    def _extract_recipient(self, header):
        """Extract recipient name and email address from header"""
        v_list = email_header.decode_header(header)
        if len(v_list) == 2:
            # User name and Email already split.
            name = str(v_list[0][0].strip())
            address = str(v_list[1][0].strip())
            address = address.replace("<", "").replace(">", "").strip()
        else:
            entry = v_list[0][0].strip()
            parsed_addr = email.utils.parseaddr(entry)

            name = parsed_addr[0]
            address = parsed_addr[1]

            if address:
                address = address.strip()

        if self.encoding:
            enc = chardet.detect(name)['encoding']
            if not enc:
                enc = 'ascii'
            name = name.decode(enc).encode(self.encoding)
        return (name, address)

    def _parse_recipients(self, header):
        """Parse header and find all recipients"""
        ret = []
        rcpt_list = self._get_recipient_list(header)
        if not rcpt_list:
            return []
        for rcpt in rcpt_list:
            (name, address) = self._extract_recipient(rcpt)
            if not name:
                name = None
            if address:
                ret.append({"name": name, "email": address})
        return ret

    @staticmethod
    def _get_content_charset(part, failobj=None):
        """Return the charset parameter of the Content-Type header.
        The returned string is always coerced to lower case.  If there is no
        Content-Type header, or if that header has no charset parameter,
        failobj is returned.
        """
        missing = object()
        charset = part.get_param("charset", missing)
        if charset is missing:
            return failobj
        if isinstance(charset, tuple):
            # RFC 2231 encoded, so decode it, and it better end up as ascii.
            pcharset = charset[0] or "us-ascii"
            try:
                # LookupError will be raised if the charset isn't known to
                # Python.  UnicodeError will be raised if the encoded text
                # contains a character not in the charset.
                charset = str(charset[2], pcharset).encode("us-ascii")
            except (LookupError, UnicodeError):
                charset = charset[2]
        # charset character must be in us-ascii range
        try:
            if isinstance(charset, str):
                charset = charset.encode("us-ascii")
            charset = unicode(charset, "us-ascii").encode("us-ascii")
        except UnicodeError:
            return failobj
        # RFC 2046, $4.1.2 says charsets are not case sensitive
        return charset.lower()

    def _parse_headers(self):
        """ Parse mail headers (include filters)"""
        self.include_headers = [x.lower() for x in self.include_headers]

        all_headers = self._get_part_headers(self.mail)
        headers = {}
        # Filter in needed headers
        for (header, value) in all_headers.items():
            if self.include_headers and \
                    header.lower() not in self.include_headers:
                continue
            else:
                headers[header] = value

        # Original headers
        self.json_data["headers"] = headers

        # Parsed headers
        self.json_data["parsed_headers"] = {}
        for header in headers.keys():
            if 'date' in header:
                self.json_data["parsed_headers"]["date"] = self._parse_date(
                    headers[header])
            elif 'subject' in header:
                self.json_data["parsed_headers"]["subject"] = \
                        self._fix_encoded_subject(headers.get("subject", None))
            elif 'message-id' in header:
                m_id = headers.get("message-id", '')
                m_id = str(m_id).replace('<', '').replace('>', '')
                self.json_data["parsed_headers"]["message-id"] = m_id
            elif header in ["from", "to", "cc", "bcc", 'reply-to']:
                data = self._parse_recipients(header)
                if 'from' or 'to' in header and len(data) >= 1:
                    # From is always only one, do not need array here.
                    data = data[0]
                self.json_data["parsed_headers"][header] = data
            else:
                self.json_data['parsed_headers'][header] = headers[header]

    @property
    def headers(self):
        output = {}
        for x in self.json_data['headers'].keys():
            output[x.title()] = self.json_data["headers"][x]
        return output

    @staticmethod
    def _parse_attachment(part):
        """Parse message attachment"""
        content_disposition = part.get("Content-Disposition", None)
        found = FILENAME_RE.findall(content_disposition)
        filename = sorted(found[0])[1] if found else "undefined"
        return dict(filename=filename, content=base64.b64encode(part.get_payload(decode=True)),
                    content_type=part.get_content_type())

    def _parse_parts(self, part):
        """Parse message part"""
        try:
            payload = part.get_payload(decode=1)
            if self.encoding:
                charset = self._get_content_charset(part, "utf-8").decode()
                content = unicode(payload,
                                  charset,
                                  "ignore").encode(self.encoding)
            else:
                content = payload
            return dict(content_type=part.get_content_type(), content=content, headers=self._get_part_headers(part))
        except LookupError:
            # Sometimes an encoding isn't recognized.
            # Not much to be done.
            pass

    def parse_mail(self):
        """Parse mail"""
        self._parse_headers()
        self.json_data['parts'] = {}
        self.json_data['attachments'] = {}
        part_count = 1
        attachment_count = 1
        for part in self.mail.walk():
            if part.is_multipart():
                continue
            content_disposition = part.get("Content-Disposition", None)
            if content_disposition:
                # We are interested in parsed attachments.
                self.json_data['attachments'][f'file{attachment_count}'] = self._parse_attachment(part)
                attachment_count += 1
            else:
                # We are interested in parsed parts.
                json_part = self._parse_parts(part)
                if json_part:
                    if json_part['content_type'] == 'text/plain':
                        self.json_data['parts']['plaintext'] = json_part
                    elif json_part['content_type'] == 'text/html':
                        self.json_data['parts']['html'] = json_part
                    else:
                        self.json_data['parts'][f'part{part_count}'] = json_part
                    self.raw_parts.append(part)
                    part_count += 1
        if self.encoding:
            self.json_data["encoding"] = self.encoding

    def to_json(self):
        return self.json_data
