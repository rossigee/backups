import subprocess
import logging

from backups.exceptions import BackupException

def encrypt(filename, passphrase):
    logging.debug("Encrypting '%s'..." % filename)
    encfilename = '%s.gpg' % filename
    encfile = open(encfilename, 'wb')
    encargs = ['gpg', '--batch', '--yes', '-q', '--passphrase-fd', '0', '-c', filename]
    encproc1 = subprocess.Popen(encargs, stdin=subprocess.PIPE, stdout=encfile, stderr=subprocess.PIPE)
    encproc1.communicate(passphrase)
    exitcode = encproc1.wait()
    if exitcode != 0:
        errmsg = encproc1.stderr.read()
        raise backups.main.BackupException("Error while encrypting: %s" % errmsg)
    encfile.close()
    return encfilename

