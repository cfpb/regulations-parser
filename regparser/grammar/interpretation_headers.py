from pyparsing import LineEnd, LineStart, SkipTo, Regex

from regparser.grammar import atomic, unified


section = (
    atomic.section_marker.copy().leaveWhitespace()
    + unified.part_section
    + SkipTo(LineEnd())
)


par = (
    atomic.section.copy().leaveWhitespace()
    + unified.depth1_p
    + SkipTo(LineEnd())
)


marker_par = (
    atomic.paragraph_marker.copy().leaveWhitespace()
    + atomic.section
    + unified.depth1_p
)

# This matches an appendix name in an appendix header. Here we'll match
# something with a dash in the appendix name (i.e. AA-1) but we'll
# remove the dash. The effect of this is that, for label purposes only,
# the appendix becomes known as 'AA1', and therefore we don't have weird
# label collisions with a node labeled '1' underneath the appendix.
appendix = (
    atomic.appendix_marker.copy().leaveWhitespace()
    + Regex(r"[A-Z]+-?[0-9]*\b").setResultsName("appendix").setParseAction(
        lambda r: r[0].replace('-', '')).setResultsName("appendix")
    + SkipTo(LineEnd())
)


parser = LineStart() + (section | marker_par | par | appendix)
