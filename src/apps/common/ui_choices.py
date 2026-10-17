"""Build suggestions from rows already authorized and loaded by the caller.

No global lookup or database query is permitted here. The view owns visibility.
"""


def text_choices(rows, attribute):
    choices = {}
    for row in rows:
        value = getattr(row, attribute, None)
        if value is None:
            continue
        text = ' '.join(str(value).split())
        if text:
            choices.setdefault(text.casefold(), text)
    return sorted(choices.values(), key=str.casefold)


def remember_form(request, key, names):
    """Retain allow-listed values for one redirect after server validation fails."""
    request.session['ui-form:'+key] = {name: request.POST.get(name, '') for name in names}


def recalled_form(request, key):
    session_key = 'ui-form:'+key
    return request.session.pop(session_key) if session_key in request.session else {}
