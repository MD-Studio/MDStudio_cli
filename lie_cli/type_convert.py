import sys
import locale
import unicodedata
import logging

logger = logging.getLogger('lie_cli')

MAJOR_PY_VERSION = sys.version_info[0]
if MAJOR_PY_VERSION < 3:
    from cStringIO import StringIO
    import urlparse
    import urllib2 as urllib
    STRING_TYPES = (str, unicode)
else:
    from io import StringIO
    from urllib import parse as urlparse
    STRING_TYPES = str


class FormatDetect(object):
    """
    Type cast string or unicode objects to float, integer or boolean.

    Uses localization to identify

    TODO: comma separated strings fail if one comma
    """

    def __init__(self, set_locale='en_US.UTF-8', decimal_point=None, thousands_sep=None):

        # Determine current localization and switch to international
        # en_US localization or other.
        self.curr_locale = locale.getdefaultlocale()
        if self.curr_locale != set_locale:
            logger.debug('Switch localization: {0} to {1}'.format('.'.join(self.curr_locale), set_locale))
            locale.setlocale(locale.LC_ALL, set_locale)

        # Register localization specific decimal and thousands seperator
        locenv = locale.localeconv()
        self.decimal_point = decimal_point or locenv['decimal_point']
        self.thousands_sep = thousands_sep or locenv['thousands_sep']

        # Register Boolean types
        self.true_types = ['true']
        self.false_types = ['false']

    @staticmethod
    def to_integer(value):

        if isinstance(value, STRING_TYPES):
            return locale.atoi(value)
        return int(value)

    @staticmethod
    def to_number(value):

        if isinstance(value, (str, unicode)):
            return locale.atof(value)
        return float(value)

    @staticmethod
    def to_string(value):

        if MAJOR_PY_VERSION < 3:
            return unicode(value)
        return value

    def to_boolean(self, value):

        if value.lower() in self.true_types:
            return True
        if value.lower() in self.false_types:
            return False

        return value

    def to_detect(self, value):

        # if string contains spaces or very long, return
        if ' ' in value or len(value) > 100:
            return value

        # str to unicode
        value = self.to_string(value)
        unicode_cats = [unicodedata.category(i)[0] for i in value]

        # Comma seperated string
        if value.count(self.thousands_sep) > 1:
            return self.to_string(value)

        # first try to convert unicode to float
        try:
            parsed = locale.atof(value)
        except ValueError:
            parsed = value

        if isinstance(parsed, float):

            # Maybe it was an integer
            allnumbers = all([n[0] == 'N' for n in unicode_cats])
            if value.isdigit() or value.isnumeric() or allnumbers:
                parsed = locale.atoi(value)
            if value.count(self.decimal_point) == 0:
                parsed = int(parsed)

            return parsed

        # Try convert unicode to integer
        try:
            parsed = self.to_integer(value)
        except ValueError:
            parsed = value

        if not isinstance(parsed, int):

            # Cases that are fully numeric with thousand seperators (e.g. 123.222.12)
            if value.count(self.decimal_point) > 1 and value.count(self.thousands_sep) == 0:
                parsed = int(value.replace(self.decimal_point, ''))

            # Unicode could be a boolean
            parsed = self.to_boolean(value)

        return parsed

    def parse(self, value, target_type=None):
        """
        Parse an unknown value to a float, integer, boolean or else
        remain in unicode.

        :param value:       value to parse
        :param target_type: type to convert to as 'integer', 'number', 'string',
                            'boolean' or automatic 'detect'
        :return:            parsed value
        """

        # target type not defined then try detect
        if not target_type:

            # if value already parsed to a type other than str or unicode return
            if not isinstance(value, STRING_TYPES):
                return value

            target_type = 'detect'

        parse_method = getattr(self, 'to_{0}'.format(target_type), None)
        if parse_method is None:
            raise AssertionError('Unknown type: {0}'.format(target_type))
        else:
            return parse_method(value)