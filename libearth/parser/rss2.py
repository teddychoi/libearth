""":mod:`libearth.parser.rss2` --- RSS 2.0 parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsing RSS 2.0 feed.

"""
try:
    from lxml import etree
except ImportError:
    try:
        from xml.etree import cElementTree as etree
    except ImportError:
        from xml.etree import ElementTree as etree

from .common import FEED, SOURCE_URL
from ..codecs import Rfc822
from ..feed import (Category, Content, Entry, Feed, Generator, Link,
                    Person, Text)

ENTRY = 3


def parse_rss(xml, feed_url=None, parse_entry=True):
    """Parse RSS 2.0 XML.

    :param xml: target rss 2.0 xml to parse
    :type xml: :class:`str`
    :param parse_item: whether to parse inner items as well.
                       it's useful to ignore items when retrieve
                       ``<source>``.  :const:`True` by default.
    :type parse_item: :class:`bool`
    :returns: a pair of (:class:`~libearth.feed.Feed`, crawler hint)
    :rtype: :class:`tuple`

    """
    root = etree.fromstring(xml)
    channel = root.find('channel')
    feed_data, crawler_hint = rss_get_channel_data(channel)
    if parse_entry:
        items = channel.findall('item')
        entry_generator = rss_get_item_data(items)
        for data in entry_generator:
            if data[0] == ENTRY:
                feed_data.entries = data[1]
            elif data[0] == SOURCE_URL:
                xml = yield data[0], data[1]
                dump = entry_generator.send(xml)
                feed_data.entries = dump[1]
    yield FEED, feed_data, crawler_hint


def rss_get_channel_data(root):
    feed_data = Feed()
    crawler_hint = {}
    contributors = []
    for data in root:
        if data.tag == 'title':
            feed_data.title = Text()
            feed_data.title.value = data.text
        elif data.tag == 'link':
            link = Link()
            link.uri = data.text
            link.relation = 'alternate'
            link.type = 'text/html'
            feed_data.links = [link]
        elif data.tag == 'description':
            subtitle = Text()
            subtitle.type = 'text'
            subtitle.value = data.text
            feed_data.subtitle = subtitle
        elif data.tag == 'copyright':
            rights = Text()
            rights.value = data.text
            feed_data.rights = rights
        elif data.tag == 'managingEditor':
            contributor = Person()
            contributor.name = data.text
            contributor.email = data.text
            contributors.append(contributor)
            feed_data.contributors = contributors
        elif data.tag == 'webMaster':
            contributor = Person()
            contributor.name = data.text
            contributor.email = data.text
            contributors.append(contributor)
            feed_data.contributors = contributors
        elif data.tag == 'pubDate':
            feed_data.updated_at = Rfc822().decode(data.text)
        elif data.tag == 'category':
            category = Category()
            category.term = data.text
            feed_data.categories = [category]
        elif data.tag == 'generator':
            generator = Generator()
            generator.value = data.text
            feed_data.generator = generator
        elif data.tag == 'lastBuildDate':
            crawler_hint['lastBuildDate'] = Rfc822().decode(data.text)
        elif data.tag == 'ttl':
            crawler_hint['ttl'] = data.text
        elif data.tag == 'skipHours':
            crawler_hint['skipHours'] = data.text
        elif data.tag == 'skipMinutes':
            crawler_hint['skipMinutes'] = data.text
        elif data.tag == 'skipDays':
            crawler_hint['skipDays'] = data.text
    return feed_data, crawler_hint


def rss_get_item_data(entries):
    entries_data = []
    for entry in entries:
        entry_data = Entry()
        links = []
        for data in entry:
            if data.tag == 'title':
                title = Text()
                title.value = data.text
                entry_data.title = title
            elif data.tag == 'link':
                link = Link()
                link.uri = data.text
                link.relation = 'alternate'
                link.type = 'text/html'
                links.append(link)
                entry_data.links = links
            elif data.tag == 'description':
                content = Content()
                content.type = 'text'
                content.value = data.text
                entry_data.content = content
            elif data.tag == 'author':
                author = Person()
                author.name = data.text
                author.email = data.text
                entry_data.authors = [author]
            elif data.tag == 'category':
                category = Category()
                category.term = data.text
                entry_data.categories = [category]
            elif data.tag == 'comments':
                #entry_data['comments'] = data.text
                pass  # FIXME
            elif data.tag == 'enclosure':
                link = Link()
                link.type = data.get('type')
                link.uri = data.get('url')
                links.append(link)
                entry_data.links = links
            elif data.tag == 'guid':
                entry_data.id = data.text
            elif data.tag == 'pubDate':
                entry_data.published = Rfc822().decode(data.text)
            elif data.tag == 'source':
                from .heuristic import get_document_type
                url = data.get('url')
                xml = yield SOURCE_URL, url
                format = get_document_type(xml)
                parser = format(xml, parse_entry=False)
                for _, source, _ in parser:
                    entry_data.source = source
                print 'source parsing finished'
        entries_data.append(entry_data)
    yield ENTRY, entries_data
