# Try to import configuration from a Python package called 'regconfig'. If
# it doesn't exist, just go with our default settings.
try:
    from regconfig import *
except ImportError:
    from regparser.default_settings import *

# Try to import a local_settings module to override parser settings. If
# it doesn't exist, we must not have needed it anyway.
try:
    from local_settings import *
except ImportError:
    pass

