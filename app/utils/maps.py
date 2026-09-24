import re

# Google's "Embed a map" dialog gives a full <iframe src="..."> snippet, not
# a bare URL. Pull the src out so we only ever store the URL, regardless of
# whether the user pasted the snippet or just the link.
_IFRAME_SRC_RE = re.compile(r'src=["\']([^"\']+)["\']')


def extract_maps_url(value: str) -> str:
    value = value.strip()
    match = _IFRAME_SRC_RE.search(value)
    if match:
        return match.group(1).strip()
    return value
