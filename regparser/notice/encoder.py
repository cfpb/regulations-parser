from json import JSONEncoder

from regparser.notice.diff import Amendment


class AmendmentEncoder(JSONEncoder):
    """Custom JSON encoder to handle Amendment objects"""
    def default(self, obj):
        if isinstance(obj, Amendment):
            return repr(obj)
        return super(AmendmentEncoder, self).default(obj)
