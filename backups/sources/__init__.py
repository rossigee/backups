# Manage list of sources as they are initialised
handlers = {}

import logging

def backupsource(id):
    def register(handler_class):
        logging.debug("Adding source '%s' as '%s'" % (handler_class, id))
        handlers[id] = handler_class
        return handler_class

    return register
