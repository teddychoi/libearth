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


class AtomPersonConstruct(ElementBase):

    def parse(self, xml_base=None):
        person = Person()
        xml_base = self._get_xml_base(xml_base)
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

    def parse(self, xml_base=None):
        link = Link()
        xml_base = self._get_xml_base(xml_base)
        link.uri = urlparse.urljoin(xml_base, self.data.get('href'))
        link.relation = self.data.get('rel')
        link.mimetype = self.data.get('type')
        link.language = self.data.get('hreflang')
        link.title = self.data.get('title')
        link.byte_size = self.data.get('length')
        return link


class AtomGenerator(ElementBase):
    element_name = 'generator'

    def parse(self, xml_base=None):
        generator = Generator()
        xml_base = self._get_xml_base(xml_base)
        generator.value = self.data.text
        if 'uri' in self.data.attrib:
            generator.uri = urlparse.urljoin(xml_base, self.data.attrib['uri'])
        generator.version = self.data.get('version')
        return generator


class AtomIcon(ElementBase):
    element_name = 'icon'

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base(xml_base)
        return urlparse.urljoin(xml_base, self.data.text)


class AtomLogo(ElementBase):
    element_name = 'logo'

    def parse(self, xml_base=None):
        xml_base = self._get_xml_base(xml_base)
        return urlparse.urljoin(xml_base, self.data.text)


class AtomContent(ElementBase):
    element_name = 'content'

    def parse(self, xml_base=None):
        content = Content()
        content.value = self.data.text
        content_type = self.data.get('type')
        if content_type is not None:
            content.type = content_type
        if 'src' in self.data.attrib:
            xml_base = self._get_xml_base(xml_base)
            content.source_uri = urlparse.urljoin(xml_base, self.data.attrib['src'])
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
    feed_data = atom_get_feed_data(root, feed_url)
    if parse_entry:
        entries = root.findall('{' + XMLNS_ATOM + '}' + 'entry')
        entries_data = atom_get_entry_data(entries, feed_url)
        feed_data.entries = entries_data
    return feed_data, None


def atom_parse_text_construct(data):
    text = Text()
    text_type = data.get('type')
    if text_type is not None:
        text.type = text_type
    if text.type in ('text', 'html'):
        text.value = data.text
    elif text.value == 'xhtml':
        text.value = ''  # TODO
    return text


def atom_parse_person_construct(data, xml_base):
    person = Person()
    xml_base = atom_get_xml_base(data, xml_base)
    for child in data:
        if child.tag == '{' + XMLNS_ATOM + '}' + 'name':
            person.name = child.text
        elif child.tag == '{' + XMLNS_ATOM + '}' + 'uri':
            person.uri = urlparse.urljoin(xml_base, child.text)
        elif child.tag == '{' + XMLNS_ATOM + '}' + 'email':
            person.email = child.text
    return person


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
                entry_data.id = AtomId(data).parse(xml_base)
            elif data.tag == AtomTitle.get_element_uri():
                entry_data.title = AtomTitle(data).parse()
            elif data.tag == AtomUpdated.get_element_uri():
                entry_data.updated_at = AtomUpdated(data).parse()
            elif data.tag == AtomAuthor.get_element_uri():
                entry_data.authors.append(AtomAuthor(data).parse(xml_base))
            elif data.tag == AtomCategory.get_element_uri():
                category = AtomCategory(data).parse()
                if category:
                    entry_data.categories.append(category)
            elif data.tag == AtomContributor.get_element_uri():
                entry_data.contributors.append(
                    AtomContributor(data).parse(xml_base)
                )
            elif data.tag == AtomLink.get_element_uri():
                entry_data.links.append(AtomLink(data).parse(xml_base))
            elif data.tag == AtomContent.get_element_uri():
                entry_data.content = AtomContent(data).parse(xml_base)
            elif data.tag == AtomPublished.get_element_uri():
                entry_data.published_at = AtomPublished(data).parse()
            elif data.tag == AtomRights.get_element_uri():
                entry_data.rigthts = AtomRights(data).parse()
            elif data.tag == '{' + XMLNS_ATOM + '}' + 'source':
                entry_data.source = atom_get_source_tag(data, xml_base)
            elif data.tag == AtomSummary.get_element_uri():
                entry_data.summary = AtomSummary(data).parse()
        entries_data.append(entry_data)
    return entries_data


def atom_get_xml_base(data, default):
    if '{' + XMLNS_XML + '}' + 'base' in data.attrib:
        return data.attrib['{' + XMLNS_XML + '}' + 'base']
    else:
        return default


def atom_get_id_tag(data, xml_base):
    xml_base = atom_get_xml_base(data, xml_base)
    return urlparse.urljoin(xml_base, data.text)


def atom_get_updated_tag(data):
    return Rfc3339().decode(data.text)


def atom_get_author_tag(data, xml_base):
    return atom_parse_person_construct(data, xml_base)


def atom_get_category_tag(data):
    if not data.get('term'):
        return
    category = Category()
    category.term = data.get('term')
    category.scheme_uri = data.get('scheme')
    category.label = data.get('label')
    return category


def atom_get_contributor_tag(data, xml_base):
    return atom_parse_person_construct(data, xml_base)


def atom_get_link_tag(data, xml_base):
    link = Link()
    xml_base = atom_get_xml_base(data, xml_base)
    link.uri = urlparse.urljoin(xml_base, data.get('href'))
    link.relation = data.get('rel')
    link.mimetype = data.get('type')
    link.language = data.get('hreflang')
    link.title = data.get('title')
    link.byte_size = data.get('length')
    return link


def atom_get_generator_tag(data, xml_base):
    generator = Generator()
    xml_base = atom_get_xml_base(data, xml_base)
    generator.value = data.text
    if 'uri' in data.attrib:
        generator.uri = urlparse.urljoin(xml_base, data.attrib['uri'])
    generator.version = data.get('version')
    return generator


def atom_get_icon_tag(data, xml_base):
    xml_base = atom_get_xml_base(data, xml_base)
    return urlparse.urljoin(xml_base, data.text)


def atom_get_logo_tag(data, xml_base):
    xml_base = atom_get_xml_base(data, xml_base)
    return urlparse.urljoin(xml_base, data.text)


def atom_get_content_tag(data, xml_base):
    content = Content()
    content.value = data.text
    content_type = data.get('type')
    if content_type is not None:
        content.type = content_type
    if 'src' in data.attrib:
        content.source_uri = urlparse.urljoin(xml_base, data.attrib['src'])
    return content


def atom_get_published_tag(data):
    return Rfc3339().decode(data.text)


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
            authors.append(AtomAuthor(data).parse(xml_base))
            source.authors = authors
        elif data.tag == AtomCategory.get_element_uri():
            category = AtomCategory(data).parse()
            if category:
                categories.append(category)
            source.categories = categories
        elif data.tag == AtomContributor.get_element_uri():
            contributors.append(AtomContributor(data).parse(xml_base))
            source.contributors = contributors
        elif data.tag == AtomLink.get_element_uri():
            links.append(AtomLink(data).parse(xml_base))
            source.links = links
        elif data.tag == AtomId.get_element_uri():
            source.id = AtomId(data).parse()
        elif data.tag == AtomTitle.get_element_uri():
            source.title = AtomTitle(data).parse()
        elif data.tag == AtomUpdated.get_element_uri():
            source.updated_at = AtomUpdated(data).parse()
        elif data.tag == AtomGenerator.get_element_uri():
            source.generator = AtomGenerator(data).parse(xml_base)
        elif data.tag == AtomIcon.get_element_uri():
            source.icon = AtomIcon(data).parse(xml_base)
        elif data.tag == AtomLogo.get_element_uri():
            source.logo = AtomLogo(data).parse(xml_base)
        elif data.tag == AtomRights.get_element_uri():
            source.rights = AtomRights(data).parse()
        elif data.tag == AtomSubtitle.get_element_uri():
            source.subtitle = AtomSubtitle(data).parse()
    return source

