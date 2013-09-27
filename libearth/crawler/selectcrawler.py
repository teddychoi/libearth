import select
import socket
from libearth.compat import PY3
if PY3:
    import urllib.parse as urlparse
else:
    import urlparse


NORMAL_FEED = 1
FEED_IN_SOURCE = 2


class FeedSocket(object):

    def __init__(self, feed_url, feed_type=NORMAL_FEED, parser=None,
                 hosts_hook_table=None):
        try:
            self.received = ''
            self.url = feed_url
            self.feed_type = feed_type
            self.parser = parser
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            url_parsed = urlparse.urlparse(feed_url)
            host = url_parsed.netloc
            if host in hosts_hook_table:
                dst = hosts_hook_table[host][0]
                port = hosts_hook_table[host][1]
            else:
                dst = host
                port = 80
            path = url_parsed.path
            self.connect((dst, port))
            send_buffer = ('GET %s HTTP/1.1\r\n' % path +
                           'Host: %s\r\n\r\n' % host)
            sent_len = 0
            while(sent_len < len(send_buffer)):
                sent_len = self.sock.send(send_buffer)
        except:
            raise ConnectError('Connect to %s failed' % host)

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def recv(self, length):
        return self.sock.recv(length)

    def content(self):
        return self.received[self.received.find('<'):
                             self.received.rfind('>')+1]


def generator(feed_list, hosts_hook_table=None):
    feeds = []
    reading_pool = []
    for feed in feed_list:
        feeds.append(FeedSocket(feed, hosts_hook_table=hosts_hook_table))
    while feeds or reading_pool:
        if len(reading_pool) != 2:
            while len(reading_pool) != 2:
                if feeds:
                    r, _, _ = select.select(feeds, [], [], 0.5)
                    if not r:
                        pass
                    else:
                        while r:
                            if len(reading_pool) is 2:
                                break
                            else:
                                feed = r.pop()
                                reading_pool.append(feed)
                                feeds.remove(feed)
                else:
                    break
        if not reading_pool:
            break
        else:
            finished = []
            has_finished = False
            while not has_finished:
                r, _, _ = select.select(reading_pool, [], [], 0.5)
                if not r:
                    finished.extend(reading_pool)
                    has_finished = True
                for feed in r:
                    just_received = feed.recv(4096)
                    if just_received:
                        feed.received = feed.received + just_received
                    else:
                        finished.append(feed)
                        has_finished = True
            for feed in finished:
                reading_pool.remove(feed)
                if feed.feed_type == NORMAL_FEED:
                    url, parser = yield feed.content()
                    if url:
                        feeds.append(FeedSocket(url, FEED_IN_SOURCE, parser,
                                                hosts_hook_table))
                elif feed.feed_type == FEED_IN_SOURCE:
                    yield feed.parser.send(feed.content())


class ConnectError(Exception):
    """Exception raised when socket connect failed."""

    def __init__(self, msg):
        self.msg = msg


class RecvFinished(Exception):
    """Exception raised when socket has no data to receive"""

    def __init__(self, msg):
        self.msg = msg
