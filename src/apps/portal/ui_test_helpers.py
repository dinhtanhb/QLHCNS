"""Role-aware GET link assertions; fragments/downloads are retained, POST never replayed."""
from html.parser import HTMLParser
from urllib.parse import urlsplit


class InternalLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '')
        target = urlsplit(href)
        if href.startswith('/') and not href.startswith('//') and not target.netloc:
            self.links.add(target.path + ('?' + target.query if target.query else ''))


def assert_internal_links(test, response):
    """Use the caller's authenticated client without following permission redirects."""
    for target in sorted(InternalLinks(response.content.decode()).links):
        with test.subTest(target=target):
            result = test.client.get(target)
            test.assertIn(result.status_code, (200, 302), target)
            if getattr(result, 'streaming', False):
                result.close()
