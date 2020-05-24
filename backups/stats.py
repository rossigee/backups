class BackupRunStatistics:
    def __init__(self):
        # Start time for backup
        self.starttime = None

        # End time for backup
        self.endtime = None

        # Final combined size of dump files
        self.size = None

        # List of filenames dumped
        self.dumpedfiles = []

        # How long the dump (and encrypt) took in seconds
        self.dumptime = None

        # How long the upload to storage took in seconds
        self.uploadtime = None

        # The list of retained backups for this job (inc this one)
        self.retained_copies = []

    def getSizeDescription(self):
        num = self.size
        for x in ['bytes','KB','MB','GB','TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0
        return "NaN"
