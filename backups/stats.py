class BackupRunStatistics:
    def __init__(self):
        # Final size of dump file
        self.size = None

        # How long the dump (and encrypt) took in seconds
        self.dumptime = None

        # How long the upload to storage took in seconds
        self.uploadtime = None

        # If known, how many retained backups for this job now (inc this one)
        self.retained_backups = None

    def getSizeDescription(self):
        num = self.size
        for x in ['bytes','KB','MB','GB','TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0
        return "NaN"
