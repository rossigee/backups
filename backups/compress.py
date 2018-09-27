import subprocess
import logging

from backups.exceptions import BackupException

def compress(filename):
    logging.info("Compressing '%s'..." % filename)
    compfilename = '%s.gzip' % filename
    comperrsname = '%s.err' % filename
    comperrs = open(comperrsname, 'wb')
    compargs = ['gzip', '--fast', filename]
    compproc1 = subprocess.Popen(compargs, stdin=subprocess.PIPE, stderr=comperrs)
    compproc1.wait()
    comperrs.close()
    exitcode = compproc1.returncode
    if exitcode != 0:
        errmsg = open(comperrsname, 'rb').read()
        raise BackupException("Error while compressing: %s" % errmsg)
    return compfilename
