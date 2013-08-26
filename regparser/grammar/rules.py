#vim: set encoding=utf-8

from regparser.grammar import common


applicable_section = (
    common.marker_part_section
    | (common.section + common.depth1_p))


applicable_appendix = common.appendix_marker + common.appendix_letter


applicable = applicable_section | applicable_appendix
