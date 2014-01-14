from json import JSONEncoder

from regparser.notice.diff import Amendment, DesignateAmendment


class AmendmentEncoder(JSONEncoder):
    """Custom JSON encoder to handle Amendment objects"""
    def default(self, obj):
        if isinstance(obj, DesignateAmendment):
            return (obj.action, obj.labels, obj.destination)
        elif isinstance(obj, Amendment):
            if obj.destination:
                return (obj.action, obj.label, obj.destination)
            else:
                return (obj.action, obj.label)
        return super(AmendmentEncoder, self).default(obj)
