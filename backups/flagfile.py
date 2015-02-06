import os, os.path

class Flagfile:
    def __init__(self, config):
        self.filename = config.get('flagfile', 'filename')
    
    def notify_success(self, name, backuptype, hostname, filename):
        f = open(self.filename, "w")
        f.write("OK")
        f.close()
    
    def notify_failure(self, name, backuptype, hostname, e):
        pass

