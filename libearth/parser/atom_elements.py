import urlparse


#: (:class:`str`) The XML namespace for Atom format.
XMLNS_ATOM = 'http://www.w3.org/2005/Atom'

#: (:class:`str`) The XML namespace for the predefined ``xml:`` prefix.
XMLNS_XML = 'http://www.w3.org/XML/1998/namespace'


class ElementBase(object):
    XMLNS = None
    element_name = None

    @classmethod
    def get_element_uri(cls):
        return '{' + cls.XMLNS + '}' + cls.element_name

    def __init__(self, data):
        self.data = data

    def parse(self):
        raise NotImplementedError('')

    def parse_with_xml_base(self, xml_base):
        raise NotImplementedError('')

    def get_xml_base(self, default):
        if '{' + XMLNS_XML + '}' + 'base' in self.data.attrib:
            return self.data.attrib['{' + XMLNS_XML + '}' + 'base']
        else:
            return default


class AtomId(ElementBase):
    XMLNS = XMLNS_ATOM
    element_name = 'id'

    def parse_with_xml_base(self, xml_base):
        xml_base = self.get_xml_base(xml_base)
        return urlparse.urljoin(xml_base, self.data.text)
