""":mod:`libearth.parser.atom` --- Atom parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsing Atom feed. Atom specification is :rfc:`4287`

.. todo::

   Parsing text construct which ``type`` is ``'xhtml'``.

"""
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from ..codecs import Rfc3339
from ..compat.etree import fromstring
from ..feed import (Category, Content, Entry, Feed, Generator, Link,
                    Person, Source, Text)
from .util import normalize_xml_encoding

__all__ = 'XMLNS_ATOM', 'XMLNS_XML', 'parse_atom'


#: (:class:`str`) The XML namespace for Atom format.
XMLNS_ATOM = 'http://www.w3.org/2005/Atom'

#: (:class:`str`) The XML namespace for the predefined ``xml:`` prefix.
XMLNS_XML = 'http://www.w3.org/XML/1998/namespace'


class ElementBase(object):
    XMLNS = XMLNS_ATOM
    element_name = None
    xml_base = None

    @classmethod
    def get_element_uri(cls):
        return '{' + cls.XMLNS + '}' + cls.element_name

    def __init__(self, data, xml_base=None):
        self.data = data
        self.xml_base = xml_base

    def parse(self):
        raise NotImplementedError('')

    def _get_xml_base(self):
        if '{' + XMLNS_XML + '}' + 'base' in self.data.attrib:
            return self.data.attrib['{' + XMLNS_XML + '}' + 'base']
        else:
            return self.xml_base


class AtomFeed(ElementBase):
    element_name = 'feed'

    def parse(self, xml_base=None):
        feed = Feed()
        feed.id = self.parse_element(AtomId) or xml_base
        feed.title = self.parse_element(AtomTitle)
        feed.updated_at = self.parse_element(AtomUpdated)
        feed.authors = self.parse_multiple_element(AtomAuthor)
        feed.categories = self.parse_multiple_element(AtomCategory)
        feed.contributors = self.parse_multiple_element(AtomContributor)
        feed.links = self.parse_multiple_element(AtomLink)
        feed.generator = self.parse_element(AtomGenerator)
        feed.icon = self.parse_element(AtomIcon)
        feed.logo = self.parse_element(AtomLogo)
        feed.rights = self.parse_element(AtomRights)
        feed.subtitle = self.parse_element(AtomSubtitle)
        return feed

    def parse_element(self, element_type):
        element = self.data.findall(element_type.get_element_uri())
        for element_ in element:
            print element_.text
        num_of_element = len(element)
        if num_of_element > 1:
            raise ValueError('Multiple {0} elements exists'.format(
                element_type.get_element_uri()
            ))
        elif num_of_element == 0:
            return None
        element = element[0]
        return element_type(element, self.xml_base).parse()

    def parse_multiple_element(self, element_type):
        elements = self.data.findall(element_type.get_element_uri())
        parsed_elements = []
        for element in elements:
            parsed_elements.append(element_type(element, self.xml_base).parse())
        return parsed_elements


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


class AtomPersonConstruct(ElementBase):
    need_xml_base = True

    def parse(self, xml_base=None):
        person = Person()
        xml_base = self._get_xml_base()
        for child in self.data:
            if child.tag == '{' + XMLNS_ATOM + '}' + 'name':
                person.name = child.text
            elif child.tag == '{' + XMLNS_ATOM + '}' + 'uri':
                person.uri = urlparse.urljoin(xml_base, child.text)
            elif child.tag == '{' + XMLNS_ATOM + '}' + 'email':
                person.email = child.text
        return person


class AtomDateConstruct(ElementBase):

    def parse(self):
        return Rfc3339().decode(self.data.text)


class AtomId(ElementBase):
    element_name = 'id'
    need_xml_base = True

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomTitle(AtomTextConstruct):
    element_name = 'title'


class AtomSubtitle(AtomTextConstruct):
    element_name = 'subtitle'


class AtomRights(AtomTextConstruct):
    element_name = 'rights'


class AtomSummary(AtomTextConstruct):
    element_name = 'summary'


class AtomAuthor(AtomPersonConstruct):
    element_name = 'author'


class AtomContributor(AtomPersonConstruct):
    element_name = 'contributor'


class AtomPublished(AtomDateConstruct):
    element_name = 'published'


class AtomUpdated(AtomDateConstruct):
    element_name = 'updated'


class AtomCategory(ElementBase):
    element_name = 'category'

    def parse(self):
        if not self.data.get('term'):
            return
        category = Category()
        category.term = self.data.get('term')
        category.scheme_uri = self.data.get('scheme')
        category.label = self.data.get('label')
        return category


class AtomLink(ElementBase):
    element_name = 'link'
    need_xml_base = True

    def parse(self, xml_base=None):
        link = Link()
        xml_base = self._get_xml_base()
        link.uri = urlparse.urljoin(xml_base, self.data.get('href'))
        link.relation = self.data.get('rel')
        link.mimetype = self.data.get('type')
        link.language = self.data.get('hreflang')
        link.title = self.data.get('title')
        link.byte_size = self.data.get('length')
        return link


class AtomGenerator(ElementBase):
    element_name = 'generator'
    need_xml_base = True

    def parse(self, xml_base=None):
        generator = Generator()
        xml_base = self._get_xml_base()
        generator.value = self.data.text
        if 'uri' in self.data.attrib:
            generator.uri = urlparse.urljoin(xml_base, self.data.attrib['uri'])
        generator.version = self.data.get('version')
        return generator


class AtomIcon(ElementBase):
    element_name = 'icon'
    need_xml_base = True

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomLogo(ElementBase):
    element_name = 'logo'
    need_xml_base = True

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base()
        return urlparse.urljoin(xml_base, self.data.text)


class AtomContent(ElementBase):
    element_name = 'content'
    need_xml_base = True

    def parse(self, xml_base=None):
        content = Content()
        content.value = self.data.text
        content_type = self.data.get('type')
        if content_type is not None:
            content.type = content_type
        if 'src' in self.data.attrib:
            xml_base = self._get_xml_base()
            content.source_uri = urlparse.urljoin(xml_base,
                                                  self.data.attrib['src'])
        return content


def parse_atom(xml, feed_url, parse_entry=True):
    """Atom parser.  It parses the Atom XML and returns the feed data
    as internal representation.

    :param xml: target atom xml to parse
    :type xml: :class:`str`
    :param feed_url: the url used to retrieve the atom feed.
                     it will be the base url when there are any relative
                     urls without ``xml:base`` attribute
    :type feed_url: :class:`str`
    :param parse_entry: whether to parse inner items as well.
                        it's useful to ignore items when retrieve
                        ``<source>`` in rss 2.0.  :const:`True` by default.
    :type parse_item: :class:`bool`
    :returns: a pair of (:class:`~libearth.feed.Feed`, crawler hint)
    :rtype: :class:`tuple`

    """
    root = fromstring(normalize_xml_encoding(xml))
    feed_data = AtomFeed(root).parse(feed_url)
    if parse_entry:
        entries = root.findall('{' + XMLNS_ATOM + '}' + 'entry')
        entries_data = atom_get_entry_data(entries, feed_url)
        feed_data.entries = entries_data
    return feed_data, None


def atom_get_feed_data(root, feed_url):
    feed_data = Feed()
    xml_base = atom_get_xml_base(root, feed_url)
    alt_id = None
    for data in root:
        if data.tag == AtomId.get_element_uri():
            feed_data.id = alt_id = AtomId(data).parse(xml_base)
        elif data.tag == AtomTitle.get_element_uri():
            feed_data.title = AtomTitle(data).parse()
        elif data.tag == AtomUpdated.get_element_uri():
            feed_data.updated_at = AtomUpdated(data).parse()
        elif data.tag == AtomAuthor.get_element_uri():
            feed_data.authors.append(AtomAuthor(data).parse(xml_base))
        elif data.tag == AtomCategory.get_element_uri():
            category = AtomCategory(data).parse()
            if category:
                feed_data.categories.append(category)
        elif data.tag == AtomContributor.get_element_uri():
            feed_data.contributors.append(
                AtomContributor(data).parse(xml_base)
            )
        elif data.tag == AtomLink.get_element_uri():
            link = AtomLink(data).parse(xml_base)
            if link.relation == 'self':
                alt_id = alt_id or link.uri
            feed_data.links.append(link)
        elif data.tag == AtomGenerator.get_element_uri():
            feed_data.generator = AtomGenerator(data).parse(xml_base)
        elif data.tag == AtomIcon.get_element_uri():
            feed_data.icon = AtomIcon(data).parse(xml_base)
        elif data.tag == AtomLogo.get_element_uri():
            feed_data.logo = AtomLogo(data).parse(xml_base)
        elif data.tag == AtomRights.get_element_uri():
            feed_data.rights = AtomRights(data).parse()
        elif data.tag == AtomSubtitle.get_element_uri():
            feed_data.subtitle = AtomSubtitle(data).parse()
        elif data.tag == '{' + XMLNS_ATOM + '}' + 'entry':
            break
    if feed_data.id is None:
        feed_data.id = alt_id or feed_url
    return feed_data


def atom_get_entry_data(entries, feed_url):
    entries_data = []
    for entry in entries:
        entry_data = Entry()
        xml_base = atom_get_xml_base(entry, feed_url)
        for data in entry:
            if data.tag == AtomId.get_element_uri():
                entry_data.id = AtomId(data, xml_base).parse()
            elif data.tag == AtomTitle.get_element_uri():
                entry_data.title = AtomTitle(data, xml_base).parse()
            elif data.tag == AtomUpdated.get_element_uri():
                entry_data.updated_at = AtomUpdated(data, xml_base).parse()
            elif data.tag == AtomAuthor.get_element_uri():
                entry_data.authors.append(AtomAuthor(data, xml_base).parse())
            elif data.tag == AtomCategory.get_element_uri():
                category = AtomCategory(data, xml_base).parse()
                if category:
                    entry_data.categories.append(category)
            elif data.tag == AtomContributor.get_element_uri():
                entry_data.contributors.append(
                    AtomContributor(data, xml_base).parse()
                )
            elif data.tag == AtomLink.get_element_uri():
                entry_data.links.append(AtomLink(data, xml_base).parse())
            elif data.tag == AtomContent.get_element_uri():
                entry_data.content = AtomContent(data, xml_base).parse()
            elif data.tag == AtomPublished.get_element_uri():
                entry_data.published_at = AtomPublished(data, xml_base).parse()
            elif data.tag == AtomRights.get_element_uri():
                entry_data.rigthts = AtomRights(data, xml_base).parse()
            elif data.tag == '{' + XMLNS_ATOM + '}' + 'source':
                entry_data.source = atom_get_source_tag(data, xml_base)
            elif data.tag == AtomSummary.get_element_uri():
                entry_data.summary = AtomSummary(data, xml_base).parse()
        entries_data.append(entry_data)
    return entries_data


def atom_get_xml_base(data, default):
    if '{' + XMLNS_XML + '}' + 'base' in data.attrib:
        return data.attrib['{' + XMLNS_XML + '}' + 'base']
    else:
        return default


def atom_get_source_tag(data_dump, xml_base):
    source = Source()
    xml_base = atom_get_xml_base(data_dump[0], xml_base)
    authors = []
    categories = []
    contributors = []
    links = []
    for data in data_dump:
        xml_base = atom_get_xml_base(data, xml_base)
        if data.tag == AtomAuthor.get_element_uri():
            authors.append(AtomAuthor(data, xml_base).parse())
            source.authors = authors
        elif data.tag == AtomCategory.get_element_uri():
            category = AtomCategory(data, xml_base).parse()
            if category:
                categories.append(category)
            source.categories = categories
        elif data.tag == AtomContributor.get_element_uri():
            contributors.append(AtomContributor(data, xml_base).parse())
            source.contributors = contributors
        elif data.tag == AtomLink.get_element_uri():
            links.append(AtomLink(data, xml_base).parse())
            source.links = links
        elif data.tag == AtomId.get_element_uri():
            source.id = AtomId(data, xml_base).parse()
        elif data.tag == AtomTitle.get_element_uri():
            source.title = AtomTitle(data, xml_base).parse()
        elif data.tag == AtomUpdated.get_element_uri():
            source.updated_at = AtomUpdated(data, xml_base).parse()
        elif data.tag == AtomGenerator.get_element_uri():
            source.generator = AtomGenerator(data, xml_base).parse()
        elif data.tag == AtomIcon.get_element_uri():
            source.icon = AtomIcon(data, xml_base).parse()
        elif data.tag == AtomLogo.get_element_uri():
            source.logo = AtomLogo(data, xml_base).parse()
        elif data.tag == AtomRights.get_element_uri():
            source.rights = AtomRights(data, xml_base).parse()
        elif data.tag == AtomSubtitle.get_element_uri():
            source.subtitle = AtomSubtitle(data, xml_base).parse()
    return source
