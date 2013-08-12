""":mod:`libearth.feed` --- Feed list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from datetime import datetime

from .compat import binary_type, text, text_type, xrange
from .schema import (Attribute, Child, Content, DocumentElement, Element, Text,
                     read, write)


class OutlineElement(Element):
    text = Attribute('text')
    title = Attribute('title')
    type_ = Attribute('type')
    xml_url = Attribute('xmlUrl')
    html_url = Attribute('htmlUrl')


OutlineElement.children = Child('outline', OutlineElement, multiple=True)


class FeedHead(Element):
    title = Text('title')

    #FIXME: replace these two to Date
    date_created = Text('dateCreated')
    date_modified = Text('dateModified')

    owner_name = Text('ownerName')
    owner_email = Text('ownerEmail')
    docs = Text('docs')
    expansion_state = Text('expansionState')
    vert_scroll_state = Text('vertScrollState', decoder=int)
    window_top = Text('windowTop', decoder=int)
    window_bottom = Text('windowBottom', decoder=int)
    window_left = Text('windowLeft', decoder=int)
    window_right = Text('windowRight', decoder=int)

    @expansion_state.decoder
    def expansion_state(self, text):
        return text.split(',')


class FeedBody(Element):
    outline = Child('outline', OutlineElement, multiple=True)


class OPMLDoc(DocumentElement):
    __tag__ = 'opml'
    head = Child('head', FeedHead)
    body = Child('body', FeedBody)


def convert_from_outline(outline_obj):
    if not outline_obj.children:
        res = {
            'title': outline_obj.title or outline_obj.text,
            'text': outline_obj.text,
            'type': outline_obj.type_,
            'html_url': outline_obj.html_url,
            'xml_url': outline_obj.xml_url,
        }
    else:
        res = {
            'type': 'category',
            'title': outline_obj.title or outline_obj.text,
            'text': outline_obj.text,
            'children': []
        }

        for outline in outline_obj.children:
            res['children'].append(convert_from_outline(outline))
    return res


def convert_to_outline(outline_dic):
    res = OutlineElement()
    if outline_dic['type'] == category:
        res.type_ = 'category'
        res.text = outline_dic['text']
        res.title = outline_dic['title']

        #TODO: add children here
    else:
        res.type_ = outline_dic['type']
        res.text = outline_dic['text']
        res.title = outline_dic['title']
        res.xml_url = outline_dic['xml_url']
        res.html_url = outline_dic['html_url']

    return res


class FeedList(object):
    def __init__(self, path=None, is_xml_string=False):
        """Initializer of Feed list
        when path is None, it doesn't save opml file. just use memory
        """
        #default value
        self.title = "EarthReader"
        #TODO: save with file, load with file
        self.path = path
        self.feedlist = {}

        if self.path:
            self.open_file(is_xml_string)

    def __len__(self):
        return len(self.feedlist)

    def __iter__(self):
        return iter(self.feedlist.values())

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
        for outline in self.doc.body.outline:
            title = outline.xml_url or outline.title or outline.text
            self.feedlist[title] = convert_from_outline(outline)

    def save_file(self, filename=None):
        self.doc.head.title = self.title

        #TODO: Change doc.body here

        now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        self.doc.head.date_modified = now
        if not self.doc.head.date_created:
            self.doc.head.date_created = now

        try:
            with open(filename or self.path, 'w') as fp:
                for chunk in write(self.doc):
                    fp.write(chunk)
        except Exception as e:
            raise SaveOPMLError()

    def get_feed(self, url):
        if not isinstance(url, text_type):
            url = text(url)

        return self.feedlist.get(url)

    def add_feed(self, url, title, type_, html_url=None, text_=None):
        if not isinstance(url, text_type):
            url = text(url)

        if url in self.feedlist:
            raise AlreadyExistException("{0} is already Exist".format(title))
        self.feedlist[url] = {
            'title': title,
            'type': type_,
            'html_url': html_url,
            'text': text_ or title,
        }

    def remove_feed(self, url):
        """Remove feed from feed list
        :returns: :const:`True` when successfuly removed.
        :const:`False` when have not to or failed to remove.
        :rtype: :class:`bool`
        """
        if url not in self.feedlist:
            return False
        else:
            self.feedlist.pop(url)
            return True


class AlreadyExistException(Exception):
    pass


class SaveOPMLError(Exception):
    pass
