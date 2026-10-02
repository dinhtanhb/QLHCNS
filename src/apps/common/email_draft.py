"""Helpers for opening reviewed email drafts in the recipient's desktop client."""
from urllib.parse import quote, urlencode


def build_mailto_url(recipient, subject, body):
    """Return a properly encoded mailto URL; this does not send mail."""
    address = quote((recipient or "").strip(), safe="@.,+_-")
    query = urlencode({"subject": subject or "", "body": body or ""}, quote_via=quote)
    return f"mailto:{address}?{query}"
