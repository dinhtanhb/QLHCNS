"""Self-contained print documents: no scripts, browser sessions or remote assets."""
import base64
from html import escape
import mimetypes
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.contrib.staticfiles import finders

from .workspace_schema import Document


def printable_html(source):
    document = Document(source).root

    def asset(value):
        path = urlsplit(value)
        prefix = settings.STATIC_URL
        if path.scheme or path.netloc or not path.path.startswith(prefix):
            return None
        name = unquote(path.path[len(prefix):])
        if '..' in PurePosixPath(name).parts or '\\' in name:
            return None
        found = finders.find(name)
        if not found or Path(found).stat().st_size > 5*1024*1024:
            return None
        return Path(found)

    def data_uri(value):
        if value.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,', 'data:font/')):
            return value
        found = asset(value)
        if not found:
            return ''
        mime = mimetypes.guess_type(str(found))[0] or 'application/octet-stream'
        return 'data:'+mime+';base64,'+base64.b64encode(found.read_bytes()).decode('ascii')

    def css(value):
        value = re.sub(r'@import\s+[^;]+;', '', value, flags=re.I)
        return re.sub(r'url\(\s*[\'"]?([^\)\'\"]+)[\'"]?\s*\)', lambda m: 'url("'+data_uri(m.group(1))+'")', value, flags=re.I)

    def render(node):
        if isinstance(node, str):
            return escape(node)
        if node.tag in {'script', 'iframe', 'object', 'embed', 'base', 'template', 'noscript', 'dialog', 'button'}:
            return ''
        if 'field-password' in node.attrs.get('class', '').split():
            return ''
        if node.tag == 'input' and node.attrs.get('type', '').lower() in {'hidden', 'password', 'submit', 'button'}:
            return ''
        if node.tag == 'meta' and node.attrs.get('http-equiv'):
            return ''
        if node.tag == 'link':
            found = asset(node.attrs.get('href', ''))
            return '<style>'+css(found.read_text(encoding='utf-8-sig'))+'</style>' if found and found.suffix == '.css' else ''
        if node.tag == 'style':
            return '<style>'+css(''.join(c for c in node.children if isinstance(c, str)))+'</style>'
        attrs = {}
        for key, value in node.attrs.items():
            if key.startswith('on') or key in {'action', 'formaction', 'href', 'target', 'nonce', 'integrity'}:
                continue
            if key == 'src':
                value = data_uri(value or '')
            if key == 'style':
                value = css(value or '')
            attrs[key] = value
        if node.tag == 'img' and not attrs.get('src'):
            return escape(node.attrs.get('alt', ''))
        attributes = ''.join(' '+key+(('="'+escape(value, quote=True)+'"') if value is not None else '') for key, value in attrs.items())
        body = ''.join(render(child) for child in node.children)
        if node.tag == 'document':
            return body
        if node.tag in Document.VOID:
            return '<'+node.tag+attributes+'>'
        return '<'+node.tag+attributes+'>'+body+'</'+node.tag+'>'

    return '<!doctype html>'+render(document)
