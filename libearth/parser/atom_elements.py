try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from ..feed import Text


#: (:class:`str`) The XML namespace for Atom format.
XMLNS_ATOM = 'http://www.w3.org/2005/Atom'

#: (:class:`str`) The XML namespace for the predefined ``xml:`` prefix.
XMLNS_XML = 'http://www.w3.org/XML/1998/namespace'


class ElementBase(object):
    XMLNS = XMLNS_ATOM
    element_name = None

    @classmethod
    def get_element_uri(cls):
        return '{' + cls.XMLNS + '}' + cls.element_name

    def __init__(self, data):
        self.data = data

    def parse(self, xml_base=None):
        raise NotImplementedError('')

    def _get_xml_base(self, default):
        if '{' + XMLNS_XML + '}' + 'base' in self.data.attrib:
            return self.data.attrib['{' + XMLNS_XML + '}' + 'base']
        else:
            return default


class AtomTextConstruct(ElementBase):

    def parse(self):
        text = Text()
        text_type = self.data.get('type')
        if text_type is not None:
            text.type = text_type
        if text.type in ('text', 'html'):
            text.value = self.data.text
        elif text.value == 'xhtml':
            text.value = ''  # TODO
        return text


class AtomId(ElementBase):
    element_name = 'id'

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base(xml_base)
        return urlparse.urljoin(xml_base, self.data.text)


class AtomTitle(AtomTextConstruct):
    element_name = 'title'


class AtomSubtitle(AtomTextConstruct):
    element_name = 'subtitle'


class AtomRights(AtomTextConstruct):
    element_name = 'rights'


class AtomSummary(AtomTextConstruct):
    element_name = 'summary'
