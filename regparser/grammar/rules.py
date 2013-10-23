#vim: set encoding=utf-8
from pyparsing import Optional, Suppress

from regparser.grammar import common


applicable_section = common.marker_part_section + Optional(common.depth1_p)


applicable_paragraph = common.section + common.depth1_p


applicable_appendix = common.appendix_marker + common.appendix_letter


applicable_interp = (
    (common.comment_marker 
        | (common.Marker('interpretations') + common.Marker('of')))
    + Optional(common.section_marker + common.part + Suppress("."))
    + common.single_comment)


applicable = (
        applicable_section 
        | applicable_paragraph
        | applicable_appendix
        | applicable_interp)
