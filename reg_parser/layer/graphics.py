from collections import defaultdict
import re

from reg_parser.layer.layer import Layer
import settings

class Graphics(Layer):
    gid = re.compile(ur'!\[([\w\s]+?)\]\(([a-zA-Z0-9.]+?)\)')

    def process(self, node):
        """If this node has a marker for an image in it, note where to get
        that image."""
        matches_by_text = defaultdict(list)
        for match in Graphics.gid.finditer(node['text']):
            matches_by_text[match.group(0)].append(match)

        layer_el = []
        for text in matches_by_text:
            match = matches_by_text[text][0]
            url = settings.IMAGE_OVERRIDES.get(match.group(2),
                    settings.DEFAULT_IMAGE_URL % match.group(2))
            layer_el.append({
                'text': match.group(0),
                'url': url,
                'alt': match.group(1),
                'locations': list(range(len(matches_by_text[text])))
            })

        if layer_el:
            return layer_el
