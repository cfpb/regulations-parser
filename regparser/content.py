"""We need to modify content from time to time, e.g. image overrides and xml
macros. To provide flexibility in future expansion, we provide a layer of
indirection here."""
import itertools
import logging

import settings


def _try_to_load(path):
    module, obj = path.rsplit('.', 1)
    try:
        #   Note: we would use importlib, but it's not available to 2.6
        module = __import__(module, fromlist=[obj])
        if hasattr(module, obj):
            return getattr(module, obj)
    except ImportError:
        logging.warning("Could not load macros from " + path)
        pass


class Macros(object):
    def __iter__(self):
        iterators = []
        for source in settings.MACROS_SOURCES:
            macros = _try_to_load(source)
            if macros:
                iterators.append(iter(macros))
        return itertools.chain(*iterators)
