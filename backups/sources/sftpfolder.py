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
        self.known_hosts_file = config.get('known_hosts_file')
        self.excludes = []
        if 'excludes' in config:
            self.excludes = config['excludes']

    def _walk(self, sftp, remote_path, excludes=None):
        if excludes is None:
            excludes = []
        dir_attrs = []
        file_attrs = []
        for attr in sftp.listdir_attr(remote_path):
            if stat.S_ISDIR(attr.st_mode):
                excluded = any(
                    fnmatch.fnmatch(attr.filename, ex) or fnmatch.fnmatch(attr.filename + '/', ex)
                    for ex in excludes
                )
                if not excluded:
                    dir_attrs.append(attr)
            else:
                file_attrs.append(attr)
        yield remote_path, dir_attrs, file_attrs
        for dattr in dir_attrs:
            yield from self._walk(sftp, '%s/%s' % (remote_path, dattr.filename), excludes)

    def dump(self):
        tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s) from %s@%s:%s...",
                     self.name, self.type, self.sshuser, self.sshhost, self.path)

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        if self.known_hosts_file:
            client.load_host_keys(self.known_hosts_file)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
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
                for root, dir_attrs, file_attrs in self._walk(sftp, self.path, self.excludes):
                    for dattr in dir_attrs:
                        arcname = os.path.relpath('%s/%s' % (root, dattr.filename), self.path)
                        info = tarfile.TarInfo(name=arcname)
                        info.type = tarfile.DIRTYPE
                        info.mtime = dattr.st_mtime
                        info.mode = stat.S_IMODE(dattr.st_mode)
                        tar.addfile(info)

                    for fattr in file_attrs:
                        remote_path = '%s/%s' % (root, fattr.filename)
                        arcname = os.path.relpath(remote_path, self.path)

                        excluded = any(
                            fnmatch.fnmatch(arcname, ex) or fnmatch.fnmatch(fattr.filename, ex)
                            for ex in self.excludes
                        )
                        if excluded:
                            continue

                        try:
                            with sftp.open(remote_path, 'rb') as f:
                                info = tarfile.TarInfo(name=arcname)
                                info.size = fattr.st_size
                                info.mtime = fattr.st_mtime
                                info.mode = stat.S_IMODE(fattr.st_mode)
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
