import string

from pyparsing import LineEnd, LineStart, SkipTo

from regparser.grammar import common


section = (
    common.Marker("section").copy().leaveWhitespace()
    + common.part_section
    + SkipTo(LineEnd())
)


par = (
    common.section.copy().leaveWhitespace()
    + common.depth1_p
    + SkipTo(LineEnd())
)


marker_par = (
    common.paragraph_marker
    + common.section
    + common.depth1_p
)


appendix = (
    common.appendix_marker.copy().leaveWhitespace()
    + common.appendix_letter
    + SkipTo(LineEnd())
)


parser = LineStart() + (section | marker_par | par | appendix)
