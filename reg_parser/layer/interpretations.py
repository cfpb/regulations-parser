from layer import Layer
from reg_parser.tree import struct

class Interpretations(Layer):
    """Supplement I (interpretations) provides (sometimes very lengthy) extra
    information about particular paragraphs. This layer provides those
    interpretations."""

    @staticmethod
    def regtext_to_interp_label(label_parts):
        """Convert a regtext label (e.g. ['99','2','b','7']) into an
        interpretation label (e.g. ['99', 'Interpretations', '2(b)(7)'])"""
        if len(label_parts) < 2:    # the root doesn't have an interp
            return

        part = label_parts[0]
        section = label_parts[1]
        paragraphs = label_parts[2:]

        interp_label = section
        if paragraphs and section.isdigit():
            interp_label += Interpretations.regtext_label(paragraphs)
        elif paragraphs:
            interp_label += Interpretations.appendix_label(paragraphs)
        return [part, 'Interpretations', interp_label]

    @staticmethod
    def regtext_label(paragraph_ids):
        """Create a label corresponding to regtext paragraphs (parens)"""
        label = ''
        for paragraph_id in paragraph_ids:
            label += '(' + paragraph_id + ')'
        return label

    @staticmethod
    def appendix_label(paragraph_ids):
        """Create a label corresponding to appendix paragraphs (dots)"""
        return '.'.join(paragraph_ids)

    def process(self, node):
        """Is there an interpretation associated with this node? If yes,
        return the associated layer information. @TODO: Right now, this only
        associates if there is a direct match. It should also associate if any
        parents match"""

        interp_label = Interpretations.regtext_to_interp_label(
                node['label']['parts'])
        if not interp_label:
            return None
        else:
            interp_label = '-'.join(interp_label)

        interpretation = struct.find(self.tree, interp_label)
        if interpretation and not self.empty_interpretation(interpretation):
            return [{
                    'text': struct.join_text(interpretation),
                    'reference': interpretation['label']['text']
                    }]  # list as we will eventually match parents as well

    def empty_interpretation(self, interpretation):
        """We don't want to include empty (e.g. \n\n) nodes as
        interpretations unless their children are subparagraphs. We 
        distinguish subparagraphs from structural children by checking for a
        title field."""
        if interpretation['text'].strip():
            return False
        if (interpretation['children'] and 
                'title' not in interpretation['children'][0]['label']):
            return False
        return True
