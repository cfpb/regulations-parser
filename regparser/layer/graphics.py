from collections import defaultdict
import re
import logging

import requests

from regparser import content
from regparser.layer.layer import Layer
import settings


class Graphics(Layer):
    gid = re.compile(ur'!\[([\w\s]*)\]\(([a-zA-Z0-9.\-]+?)\)')

    def check_for_thumb(self, url):
        thumb_url = re.sub(r'(.(png|gif|jpg))$', '.thumb' + '\\1', url)

        try:
            response = requests.head(thumb_url)
        except:
            logging.warning("Error fetching %s" % thumb_url)
            return

        if response.status_code == requests.codes.not_implemented:
            response = requests.get(thumb_url)

        if response.status_code == requests.codes.ok:
            return thumb_url

    def process(self, node):
        """If this node has a marker for an image in it, note where to get
        that image."""
        matches_by_text = defaultdict(list)
        for match in Graphics.gid.finditer(node.text):
            matches_by_text[match.group(0)].append(match)

        layer_el = []
        for text in matches_by_text:
            match = matches_by_text[text][0]
            url = content.ImageOverrides().get(
                match.group(2), settings.DEFAULT_IMAGE_URL % match.group(2))
            layer_el_vals = {
                'text': match.group(0),
                'url': url,
                'alt': match.group(1),
                'locations': list(range(len(matches_by_text[text])))
            }
            thumb_url = self.check_for_thumb(url)

            if thumb_url:
                layer_el_vals['thumb_url'] = thumb_url
            layer_el.append(layer_el_vals)

        if layer_el:
            return layer_el
