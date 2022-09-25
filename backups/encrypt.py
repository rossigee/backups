import os
import subprocess
import logging

from backups.exceptions import BackupException

def encrypt(filename, passphrase=None, recipients=None):
    logging.info("Encrypting '%s'..." % filename)
    encfilename = '%s.gpg' % filename
    encerrsname = '%s.err' % filename
    encfile = open(encfilename, 'wb')
    encerrs = open(encerrsname, 'wb')
    encargs = ['gpg', '--batch', '--yes', '-q']
    if recipients is not None:
        encargs += ['--trust-model', 'always', '--encrypt']
        for r in recipients:
            encargs += ['-r', r]
    elif passphrase is not None:
        encargs += ['--passphrase-fd', '0', '--symmetric']
    else:
        raise BackupException("Misconfigured encryption")
    encargs += [filename]
    encenv = os.environ.copy()
    encproc1 = subprocess.Popen(encargs, stdin=subprocess.PIPE, stdout=encfile, stderr=encerrs, env=encenv)
    if passphrase is not None:
        encproc1.communicate(passphrase.encode('utf8'))
    encproc1.wait()
    encfile.close()
    encerrs.close()
    exitcode = encproc1.returncode
    if exitcode != 0:
        errmsg = open(encerrsname, 'rb').read()
        raise BackupException("Error while encrypting: %s" % errmsg)
    return encfilename
