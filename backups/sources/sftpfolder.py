import os, os.path
import stat
import fnmatch
import logging
import tarfile

import paramiko

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException


@backupsource('sftp-folder')
class SFTPFolder(BackupSource):
    def __init__(self, config, type="SFTPFolder"):
        BackupSource.__init__(self, config, type, "tar.gpg")
        self.sshhost = config['sshhost']
        self.sshuser = config['sshuser']
        self.sshport = int(config.get('sshport', 22))
        self.path = config['path'].rstrip('/')
        self.password = config.get('password')
        self.key_filename = config.get('key_filename')
        self.excludes = []
        if 'excludes' in config:
            self.excludes = config['excludes']

    def _walk(self, sftp, remote_path):
        dirs = []
        files = []
        for attr in sftp.listdir_attr(remote_path):
            if stat.S_ISDIR(attr.st_mode):
                dirs.append(attr.filename)
            else:
                files.append(attr.filename)
        yield remote_path, dirs, files
        for d in dirs:
            yield from self._walk(sftp, '%s/%s' % (remote_path, d))

    def dump(self):
        tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s) from %s@%s:%s...",
                     self.name, self.type, self.sshuser, self.sshhost, self.path)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            connect_kwargs = {
                'hostname': self.sshhost,
                'port': self.sshport,
                'username': self.sshuser,
            }
            if self.password:
                connect_kwargs['password'] = self.password
            if self.key_filename:
                connect_kwargs['key_filename'] = self.key_filename
            client.connect(**connect_kwargs)

            sftp = client.open_sftp()
            with tarfile.open(tarfilename, 'w') as tar:
                for root, dirs, files in self._walk(sftp, self.path):
                    for fname in files:
                        remote_path = '%s/%s' % (root, fname)
                        arcname = os.path.relpath(remote_path, self.path)

                        excluded = False
                        for exclude in self.excludes:
                            if fnmatch.fnmatch(arcname, exclude) or fnmatch.fnmatch(fname, exclude):
                                excluded = True
                                break
                        if excluded:
                            continue

                        try:
                            attr = sftp.stat(remote_path)
                            with sftp.open(remote_path, 'rb') as f:
                                info = tarfile.TarInfo(name=arcname)
                                info.size = attr.st_size
                                info.mtime = attr.st_mtime
                                info.mode = stat.S_IMODE(attr.st_mode)
                                tar.addfile(info, f)
                        except Exception as e:
                            raise BackupException(
                                "Error downloading '%s' via SFTP: %s" % (remote_path, e))
        except BackupException:
            raise
        except Exception as e:
            raise BackupException("SFTP connection error: %s" % e)
        finally:
            client.close()

        return [tarfilename, ]
