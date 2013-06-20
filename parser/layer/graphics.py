from collections import defaultdict
from parser.layer.layer import Layer
import re

class Graphics(Layer):
    gid = re.compile(ur'<GID>(.*?)</GID>', re.IGNORECASE)

    def process(self, node):
        """If this node has a marker for an image in it, note where to get
        that image."""
        matches_by_text = defaultdict(list)
        for match in Graphics.gid.finditer(node['text']):
            matches_by_text[match.group(0)].append(match)

        layer_el = []
        for text in matches_by_text:
            match = matches_by_text[text][0]
            layer_el.append({
                'text': match.group(0),
                'url': ('https://s3.amazonaws.com/images.federalregister.gov/'
                    + match.group(1) + '/original.gif'),
                'locations': list(range(len(matches_by_text[text])))
            })

        if layer_el:
            return layer_el
