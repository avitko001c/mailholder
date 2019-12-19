from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class IntegerValidator(RegexValidator):
	def __init__(self, regex=None, message=None, code=None, inverse_match=None, flags=None):
		super(IntegerValidator, self).__init__(regex, message, code, inverse_match, flags)

	def __call__(self, value):
		if not isinstance(value, int):
			from django.core.validators import ValidationError
			value_type = type(value)
			raise ValidationError("Requires a type of <class 'int'> not {}".format(value_type), code=self.code)
		super(IntegerValidator, self).__call__(value)

integer_validator = IntegerValidator(
    _lazy_re_compile(r'^-?\d+\Z'),
    message=_('Enter a valid integer.'),
    code='invalid',
)
