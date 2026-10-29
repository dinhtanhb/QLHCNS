"""Translate server-rendered form contracts to native controls, never executable HTML."""
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def descendants(self, *tags):
        for child in self.children:
            if isinstance(child, Node):
                if not tags or child.tag in tags:
                    yield child
                yield from child.descendants(*tags)

    def text(self):
        if self.tag in {'script', 'style', 'svg', 'template'} or self.attrs.get('aria-hidden') == 'true':
            return ''
        return re.sub(r'\s+', ' ', ' '.join(c.text() if isinstance(c, Node) else c for c in self.children)).strip()


class Document(HTMLParser):
    VOID = {'input', 'br', 'hr', 'img', 'meta', 'link', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


class NativeSchema:
    def __init__(self, html, path, allowed, origin=''):
        self.document = Document(html).root
        self.path = path
        self.allowed = allowed
        self.origin = urlsplit(origin).netloc.lower()
        self.labels = {n.attrs.get('for'): n.text() for n in self.document.descendants('label') if n.attrs.get('for')}
        self.disabled_controls = set()
        for fieldset in self.document.descendants('fieldset'):
            if 'disabled' in fieldset.attrs:
                self.disabled_controls.update(id(n) for n in fieldset.descendants('input', 'select', 'textarea', 'button'))
        self.counter = 0
        self.references = {}
        reference_node = next((n for n in self.document.descendants('script') if n.attrs.get('id') == 'hcns-reference-data'), None)
        if reference_node:
            try:
                data = json.loads(''.join(c for c in reference_node.children if isinstance(c, str)))
                if isinstance(data, dict):
                    self.references = data
            except ValueError:
                pass
        for script_id, pool, target in [('task-code-names', 'task_codes', 'task_name'), ('activity-code-names', 'activity_codes', 'activity_name')]:
            node = next((n for n in self.document.descendants('script') if n.attrs.get('id') == script_id), None)
            if node:
                try:
                    names = json.loads(''.join(c for c in node.children if isinstance(c, str)))
                    if isinstance(names, dict):
                        self.references[pool] = {str(code): {target: name} for code, name in names.items() if isinstance(name, str)}
                except ValueError:
                    pass

    def href(self, value):
        if not isinstance(value, str) or not value or value.startswith('#'):
            return None
        target = urlsplit(urljoin(self.path, value))
        if target.scheme in {'https', 'http', 'mailto', 'tel'} and not (self.origin and target.netloc.lower() == self.origin and target.scheme in {'http', 'https'}):
            return {'path': value, 'external': True}
        query = target.query
        if target.path.startswith('/admin/'):
            # Django's related-object popup ends with browser-only JS. Native
            # navigation uses the ordinary add/change page and redirect instead.
            query = urlencode([(key, value) for key, value in parse_qsl(query, keep_blank_values=True) if key != '_popup'])
        path = target.path + ('?'+query if query else '')
        if self.allowed(path):
            return {'path': path, 'external': False}
        return None

    def link(self, node):
        target = self.href(node.attrs.get('href'))
        if target and node.text():
            return {'kind': 'link', 'label': node.text(), **target}
        return None

    def control(self, node, index):
        attrs = node.attrs
        name = attrs.get('name')
        if not name or name == 'csrfmiddlewaretoken':
            return None
        kind = attrs.get('type', 'text').lower() if node.tag == 'input' else node.tag
        if kind in {'submit', 'button', 'reset', 'image'}:
            return None
        label = attrs.get('aria-label') or self.labels.get(attrs.get('id')) or attrs.get('placeholder') or name.replace('_', ' ')
        value = attrs.get('value') or ''
        if kind == 'textarea':
            value = ''.join(c if isinstance(c, str) else c.text() for c in node.children)
        options = []
        if kind == 'select':
            options = [{'label': option.text(), 'value': option.attrs.get('value', option.text()),
                        'disabled': 'disabled' in option.attrs, 'selected': 'selected' in option.attrs}
                       for option in node.descendants('option')]
            selected = [option['value'] for option in options if option['selected']]
            value = selected if 'multiple' in attrs else (selected[0] if selected else options[0]['value'] if options else '')
        elif kind in {'checkbox', 'radio'}:
            value = attrs.get('value', 'on')
        if kind == 'password':
            value = ''
        remote = None
        if attrs.get('data-ajax--url'):
            target = self.href(attrs['data-ajax--url'])
            if target and not target['external']:
                remote = target['path'] + ('&' if '?' in target['path'] else '?') + urlencode({
                    'app_label': attrs.get('data-app-label', ''), 'model_name': attrs.get('data-model-name', ''),
                    'field_name': attrs.get('data-field-name', '')})
        return {'id': str(index), 'name': name, 'type': kind, 'label': label,
                'value': value, 'options': options, 'checked': 'checked' in attrs,
                'disabled': 'disabled' in attrs or id(node) in self.disabled_controls, 'readonly': 'readonly' in attrs,
                'required': 'required' in attrs, 'multiple': 'multiple' in attrs,
                'placeholder': attrs.get('placeholder', ''),
                'remote': remote,
                'reference': attrs.get('data-reference') or ('task_codes' if name == 'act_code' and 'task_codes' in self.references else 'activity_codes' if name == 'activity_code' and 'activity_codes' in self.references else None),
                'referenceKey': attrs.get('data-reference-key') or ('code' if name in {'act_code', 'activity_code'} else None),
                'numericLocale': kind == 'number' and attrs.get('data-ui-number') != 'plain' and not re.search(r'(?:^|[_-])(?:year|month|day)(?:$|[_-])', name),
                'maxLength': int(attrs['maxlength']) if str(attrs.get('maxlength', '')).isdigit() else None,
                'min': attrs.get('min'), 'max': attrs.get('max'), 'step': attrs.get('step'),
                'accept': attrs.get('accept', '')}

    def form(self, node):
        self.counter += 1
        target = self.href(node.attrs.get('action') or self.path)
        if not target or target['external']:
            return {'kind': 'text', 'text': 'Biểu mẫu này có địa chỉ xử lý ngoài phạm vi ứng dụng.'}
        fields = [self.control(n, index) for index, n in enumerate(node.descendants('input', 'select', 'textarea'))]
        fields = [f for f in fields if f]
        templates = {}
        regular = []
        for f in fields:
            if '-__prefix__-' in f['name']:
                prefix = f['name'].split('-__prefix__-', 1)[0]
                templates.setdefault(prefix, []).append(f)
            else:
                regular.append(f)
        actions = []
        has_submit = False
        for button in node.descendants('button', 'input'):
            kind = button.attrs.get('type', 'submit' if button.tag == 'button' else 'text').lower()
            print_preview = button.attrs.get('id') == 'hcns-print'
            if kind not in {'submit', 'image'} and not print_preview:
                continue
            has_submit = True
            if 'disabled' in button.attrs or id(button) in self.disabled_controls:
                continue
            action = self.href(button.attrs.get('formaction') or target['path'])
            if not action or action['external']:
                continue
            actions.append({'label': button.text() or button.attrs.get('value') or 'Gửi',
                            'name': 'action' if print_preview else button.attrs.get('name', ''), 'value': 'preview' if print_preview else button.attrs.get('value', ''),
                            'path': action['path'], 'method': button.attrs.get('formmethod', node.attrs.get('method', 'get')).upper(),
                            'confirm': button.attrs.get('data-ui-confirm') or node.attrs.get('data-ui-confirm') or '', 'print': print_preview})
        if not actions and not has_submit:
            actions = [{'label': 'Áp dụng' if node.attrs.get('method', 'get').lower() == 'get' else 'Lưu',
                        'name': '', 'value': '', 'path': target['path'],
                        'method': node.attrs.get('method', 'get').upper(), 'confirm': node.attrs.get('data-ui-confirm', '')}]
        repeats = []
        if any(n.attrs.get('id') == 'add-procurement-item' for n in node.descendants('button')):
            repeats = [f for f in regular if f['name'] in {'item_name', 'quantity', 'estimated_cost'}]
        return {'kind': 'form', 'id': str(self.counter), 'path': target['path'], 'fields': regular,
                'templates': templates, 'repeat': repeats, 'references': self.references, 'actions': actions, 'blocks': self.walk_children(node, inside_form=True)}

    def walk_children(self, node, inside_form=False):
        result = []
        for child in node.children:
            if isinstance(child, Node):
                result.extend(self.walk(child, inside_form))
            elif child.strip():
                result.append({'kind': 'text', 'text': child.strip()})
        return result

    def walk(self, node, inside_form=False):
        classes = set(node.attrs.get('class', '').split())
        if node.tag in {'script', 'style', 'svg', 'template', 'dialog', 'noscript'} or 'hidden' in node.attrs or node.attrs.get('aria-hidden') == 'true':
            return []
        if 'empty-form' in classes or 'field-password' in classes or 'ui-print-only' in classes or 'print-only' in classes:
            return []
        if node.attrs.get('aria-label') == 'Thông báo hệ thống':
            return []  # Delivered once through the response's structured messages.
        if classes.intersection({'ui-error-summary', 'ui-field-error', 'errorlist', 'errornote'}) or node.attrs.get('role') == 'alert':
            return [{'kind': 'notice', 'text': node.text()}] if node.text() else []
        if node.tag in {'a', 'button', 'input'} and ('window.print(' in node.attrs.get('onclick', '') or node.attrs.get('id') == 'hcns-print'):
            if inside_form and node.attrs.get('id') == 'hcns-print':
                return []
            return [{'kind': 'print', 'label': node.text() or node.attrs.get('value') or 'In / lưu PDF', 'path': self.path}]
        if node.tag == 'form':
            return [self.form(node)]
        if node.tag in {'input', 'select', 'textarea', 'button', 'label'}:
            return []
        if node.tag == 'a':
            value = self.link(node)
            return [value] if value else ([{'kind': 'text', 'text': node.text()}] if node.text() else [])
        if node.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            return [{'kind': 'heading', 'text': node.text()}] if node.text() else []
        if node.tag == 'table':
            if inside_form:
                return self.walk_children(node, inside_form=True)
            head = next(node.descendants('thead'), None)
            if head is None:
                first = next(node.descendants('tr'), None)
                head = first if first and not any(first.descendants('td')) else None
            heads = [n.text() for n in head.descendants('th')] if head else []
            rows = []
            for row in node.descendants('tr'):
                if set(row.attrs.get('class', '').split()).intersection({'ui-print-only', 'print-only'}):
                    continue
                cells = [n for n in row.children if isinstance(n, Node) and n.tag in {'td', 'th'}]
                if not any(cell.tag == 'td' for cell in cells):
                    continue
                links = [self.link(n) for n in row.descendants('a')]
                # Legacy asset lists use a constant location assignment instead
                # of an anchor. Recognize only that exact contract; never run JS.
                destination = re.fullmatch(r"\s*window\.location\s*=\s*(['\"])(/[^'\"]*)\1\s*;?\s*", row.attrs.get('onclick', ''))
                if destination:
                    target = self.href(destination.group(2))
                    if target and not target['external']:
                        links.append({'kind': 'link', 'label': 'Mở chi tiết', **target})
                forms = [self.form(n) for n in row.descendants('form')]
                rows.append({'cells': [{'label': heads[index] if index < len(heads) else '', 'text': cell.text()}
                                       for index, cell in enumerate(cells)],
                             'blocks': [link for link in links if link] + forms})
            caption = next(node.descendants('caption'), None)
            return ([{'kind': 'heading', 'text': caption.text()}] if caption and caption.text() else []) + ([{'kind': 'table', 'rows': rows}] if rows else [])
        if node.tag in {'p', 'li', 'dd', 'dt', 'legend', 'pre'} and not any(node.descendants('form', 'input', 'select', 'textarea')):
            result = [{'kind': 'text', 'text': node.text()}] if node.text() else []
            return result + [link for link in (self.link(n) for n in node.descendants('a')) if link]
        if node.tag == 'img':
            return [{'kind': 'text', 'text': node.attrs['alt']}] if node.attrs.get('alt') else []
        return self.walk_children(node, inside_form)

    def result(self):
        main = next((n for n in self.document.descendants() if n.attrs.get('id') in {'main-content', 'content-main'}), None)
        if main is None:
            main = next((n for n in self.document.descendants() if n.attrs.get('id') == 'content'), None)
        if main is None:
            main = next(self.document.descendants('body'), self.document)
        title = next(self.document.descendants('title'), None)
        navigation = []
        sidebar = next((n for n in self.document.descendants() if n.attrs.get('id') == 'portalSidebar'), None)
        if sidebar:
            seen = set()
            groups = {}
            for group in sidebar.descendants('div'):
                if 'ui-nav-group' in group.attrs.get('class', '').split():
                    trigger = next(group.descendants('button'), None)
                    for link in group.descendants('a'):
                        groups[id(link)] = trigger.text() if trigger else 'Nghiệp vụ'
            for node in sidebar.descendants('a'):
                link = self.link(node)
                if link and link['path'] not in seen:
                    link['group'] = groups.get(id(node), 'Tổng quan')
                    seen.add(link['path']); navigation.append(link)
        seen = {link['path'] for link in navigation}
        for node in self.document.descendants('a'):
            link = self.link(node)
            if link and not link['external'] and link['path'].split('?')[0] in {'/admin/', '/assistant/', '/reports/'} and link['path'] not in seen:
                link['group'] = 'Quản trị' if link['path'].startswith('/admin/') else 'Tra cứu và báo cáo'
                seen.add(link['path']); navigation.append(link)
        return {'kind': 'page', 'path': self.path, 'title': title.text() if title else 'IHRMS',
                'blocks': self.walk_children(main), 'navigation': navigation}
