# Manage list of notifications as they are initialised
handlers = {}

import logging

def backupnotification(id):
    def register(handler_class):
        logging.debug("Adding notification '%s' as '%s'" % (handler_class, id))
        handlers[id] = handler_class
        return handler_class

    return register
