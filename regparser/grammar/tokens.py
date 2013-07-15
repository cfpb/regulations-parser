class Verb:
    def __init__(self, verb, active):
        self.verb = verb
        self.active = active
    def __repr__(self):
        return "Verb( '%s', active=%s )" % (self.verb, self.active)


class Subpart:
    def __init__(self, subpart):
        self.subpart = subpart
    def __repr__(self):
        return "Subpart( '%s' )" % self.subpart


class Section:
    def __init__(self, part, section):
        self.part = part
        self.section = section
    def __repr__(self):
        return "Section( '%s', '%s' )" % (self.part, self.section)

class ParagraphList:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs
    def __repr__(self):
        return "ParagraphList([ %s ])" % ', '.join(map(repr,
            self.paragraphs))

class Paragraph:
    def __init__(self, part=None, section=None, level1=None, level2=None,
            level3=None, level4=None, text=False):
        def none_or(attr, value):
            if not value:
                value = None
            setattr(self, attr, value)

        none_or('part', part)
        none_or('section', section)
        none_or('level1', level1)
        none_or('level2', level2)
        none_or('level3', level3)
        none_or('level4', level4)
        self.text = text

    def __repr__(self):
        def none_str(value):
            if value is None:
                return 'None'
            else:
                return "'%s'" % value
        return "Paragraph( %s, %s, %s, %s, %s, %s, text=%s )" % (
                none_str(self.part), none_str(self.section),
                none_str(self.level1), none_str(self.level2),
                none_str(self.level3), none_str(self.level4), self.text)

    def clone(self, part=None, section=None, level1=None, level2=None,
            level3=None, level4=None, text=False):
        return Paragraph(part or self.part, section or self.section,
                level1 or self.level1, level2 or self.level2, 
                level3 or self.level3, level4 or self.level4)

    def as_list(self):
        return [self.part, self.section, self.level1, self.level2,
                self.level3, self.level4]

    def id(self, context):
        id_parts = [None] * 6
        context = context or []
        for i in range(len(context)):
            id_parts[i] = context[i]
        as_list = self.as_list()

        found_start = False
        for i in range(len(as_list)):
            if not as_list[i] and not found_start:
                continue
            elif as_list[i]:
                found_start = True
            id_parts[i] = as_list[i]
        
        return [part for part in id_parts if part is not None]


class SectionHeading:
    def __repr__(self):
        return "SectionHeading()"


class SectionHeadingOf:
    def __repr__(self):
        return "SectionHeadingOf()"


class IntroText:
    def __repr__(self):
        return "IntroText()"
