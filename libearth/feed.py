""":mod:`libearth.feed` --- Feed list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from abc import ABCMeta, abstractmethod
import collections
from datetime import datetime

from .compat import binary_type, text, text_type, xrange
from .schema import (Attribute, Child, Content, DocumentElement, Element, Text,
                     read, write)


class FeedTree():
    __metaclass__ = ABCMeta

    def __init__(self, type, title):
        self.type = type
        self.title = title


class FeedCategory(FeedTree, collections.MutableSequence):
    type = 'category'

    def __init__(self, title, text=None):
        super(FeedCategory, self).__init__('category', title)
        self.text = text
        self.children = []

        #for not allowing same feed on same category
        self.urls = []

    def append(self, obj):
        if not isinstance(obj, FeedTree):
            raise TypeError('class is must be instance of FeedTree')
        if obj.type == 'feed':
            if obj.xml_url in self.urls:
                raise AlreadyExistException(
                    "{0} is already here".format(obj.title)
                )
            else:
                self.urls.append(obj.xml_url)

        self.children.append(obj)

    def insert(self, index, value):
        if not isinstance(obj, FeedTree):
            raise TypeError('class is must be instance of FeedTree')

        self.children.insert(index, value)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __setitem__(self, index, value):
        if not isinstance(value, FeedTree):
            raise TypeError('class is must be instance of FeedTree')
        self.children[index] = value

    def __delitem__(self, index):
        del self.children[index]


class Feed(FeedTree):
    def __init__(self, rsstype, title, xml_url, html_url=None, text=None):
        super(Feed, self).__init__('feed', title)
        self.rsstype = rsstype
        self.xml_url = xml_url
        self.html_url = html_url
        self.text = text or title


class OutlineElement(Element):
    text = Attribute('text')
    title = Attribute('title')
    type = Attribute('type')
    xml_url = Attribute('xmlUrl')
    html_url = Attribute('htmlUrl')

    children = Child('outline', 'OutlineElement', multiple=True)


class HeadElement(Element):
    title = Text('title')

    #FIXME: replace these two to Date
    date_created = Text('dateCreated')
    date_modified = Text('dateModified')

    owner_name = Text('ownerName')
    owner_email = Text('ownerEmail')
    docs = Text('docs')
    expansion_state = Text('expansionState')
    vert_scroll_state = Text('vertScrollState', decoder=int, encoder=str)
    window_top = Text('windowTop', decoder=int, encoder=str)
    window_bottom = Text('windowBottom', decoder=int, encoder=str)
    window_left = Text('windowLeft', decoder=int, encoder=str)
    window_right = Text('windowRight', decoder=int, encoder=str)

    @expansion_state.decoder
    def expansion_state(self, text):
        return text.split(',')

    @expansion_state.encoder
    def expansion_state(self, obj):
        if not obj:
            res = ""
        else:
            res = ','.join(obj)
        return res


class BodyElement(Element):
    outline = Child('outline', OutlineElement, multiple=True)


class OPMLDoc(DocumentElement):
    __tag__ = 'opml'
    head = Child('head', HeadElement)
    body = Child('body', BodyElement)


class FeedList(object):
    """FeedList is Class for OPML file
    it has a dictionary named :var:`all_feeds` which have all :class:`Feed` for
    linked on multi :class:`FeedCategory`
    :var:`all_feeds` is hashed with tuple key: (type, title, xml_url)
    """
    def __init__(self, path=None, is_xml_string=False):
        """Initializer of Feed list
        when path is None, it doesn't save opml file. just use memory
        """
        #TODO: same Feed on multiple category
        #TODO: Only one feed on same category

        #default value
        self.title = "EarthReader"

        self.path = path
        self.feedlist = FeedCategory(self.title)
        self.all_feeds = {}

        if self.path:
            self.open_file(is_xml_string)

    def open_file(self, is_xml_string):
        if is_xml_string:
            xml = self.path
            self.doc = read(OPMLDoc, xml)
            self.parse_doc()
        else:
            try:
                with open(self.path) as fp:
                    xml = fp.read()
                    self.doc = read(OPMLDoc, xml)
            except IOError as e:
                raise e
            else:
                self.parse_doc()

    def parse_doc(self):
        self.title = self.doc.head.title
        self.owner_name = self.doc.head.owner_name
        self.owner_email = self.doc.head.owner_email
        self.docs = self.doc.head.docs
        self.expansion_state = self.doc.head.expansion_state
        self.vert_scroll_state = self.doc.head.vert_scroll_state

        self.window_top = self.doc.head.window_top
        self.window_left = self.doc.head.window_left
        self.window_bottom = self.doc.head.window_bottom
        self.window_right = self.doc.head.window_right

        self.date_created = self.doc.head.date_created
        self.date_modified = self.doc.head.date_modified

        for outline in self.doc.body.outline:
            self.feedlist.append(self.convert_from_outline(outline))

    def save_file(self, filename=None):
        self.doc.head.title = self.title
        self.doc.head.owner_name = self.owner_name
        self.doc.head.owner_email = self.owner_email
        self.doc.head.docs = self.docs
        self.doc.head.expansion_state = self.expansion_state
        self.doc.head.vert_scroll_state = self.vert_scroll_state

        self.doc.head.window_top = self.window_top
        self.doc.head.window_left = self.window_left
        self.doc.head.window_bottom = self.window_bottom
        self.doc.head.window_right = self.window_right

        #TODO: Change doc.body here
        self.doc.body.outline[:] = []
        for feed in self.feedlist:
            self.doc.body.outline.append(self.convert_to_outline(feed))

        now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        self.doc.head.date_modified = now
        if not self.doc.head.date_created:
            self.doc.head.date_created = now

        try:
            filename = filename or self.path
            with open(filename, 'w') as fp:
                for chunk in write(self.doc):
                    fp.write(chunk)
        except Exception as e:
            raise SaveOPMLError(e.message)

    def add_feed(self, type, title, xml_url, html_url=None, text=None):
        feed = self.make_feed(type, title, xml_url, html_url, text)
        self.feedlist.append(feed)

    def append(self, feed):
        key = (feed.type, feed.title, feed.xml_url)
        if key in self.all_feeds:
            orig_feed = self.all_feeds.get(key)
            self.feedlist.append(orig_feed)

            orig_feed.html_url = feed.html_url
            orig_feed.text = feed.text
        else:
            self.feedlist.append(feed)

    def make_feed(self, type, title, xml_url, html_url=None, text=None):
        """pick from all_feeds or make feed for multiple linking"""

        text = text or title

        key = (type, title, xml_url)

        feed = self.all_feeds.get(key)
        if feed:
            feed.html_url = html_url
            feed.text = text
        else:
            feed = Feed(type, title, xml_url, html_url, text)
            self.all_feeds[key] = feed

        return feed

    def convert_from_outline(self, outline_obj):
        if outline_obj.children:
            title = outline_obj.title or outline_obj.text

            res = FeedCategory(title)

            for outline in outline_obj.children:
                feed = self.convert_from_outline(outline)
                res.append(self.convert_from_outline(outline))
        else:
            type = outline_obj.type
            title = outline_obj.title or outline_obj.text
            xml_url = outline_obj.xml_url
            html_url = outline_obj.html_url
            text = outline_obj.text

            res = self.make_feed(type, title, xml_url, html_url, text)

        return res

    def convert_to_outline(self, feed_obj):
        res = OutlineElement()
        if feed_obj.type == 'category':
            res.type = 'category'
            res.text = feed_obj.text
            res.title = feed_obj.title

            res.children = []
            for child in feed_obj:
                res.children.append(self.convert_to_outline(child))
        else:
            res.type = feed_obj.rsstype
            res.text = feed_obj.text
            res.title = feed_obj.title
            res.xml_url = feed_obj.xml_url
            res.html_url = feed_obj.html_url

        return res

    def __len__(self):
        return len(self.feedlist)

    def __iter__(self):
        return iter(self.feedlist)

    def __getitem__(self, key):
        return self.feedlist[key]

    def __setitem__(self, key, value):
        self.feedlist[key] = value

    def __delitem__(self, key):
        del self.feedlist[key]


class AlreadyExistException(Exception):
    def __init__(self, message):
        super(AlreadyExistException, self).__init__(message)


class SaveOPMLError(Exception):
    def __init__(self, message):
        super(SaveOPMLError, self).__init__(message)
