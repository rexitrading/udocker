# -*- coding: utf-8 -*-
"""Management and tools for the keystore"""

import os
import json

from udocker.utils.fileutil import FileUtil


class KeyStore(object):
    """Basic storage for authentication tokens to be used
    with dockerhub and private repositories
    """

    def __init__(self, conf, keystore_file):
        """Initialize keystone"""
        self.conf = conf
        self.keystore_file = keystore_file
        self.credential = dict()

    def get(self, url):
        """Get credential from keystore for given url"""
        auths = self._read_all()
        try:
            self.credential = auths[url]
            return self.credential["auth"]
        except KeyError:
            pass
        return ""

    def put(self, url, credential, email):
        """Put credential in keystore for given url"""
        if not credential:
            return False
        auths = self._read_all()
        auths[url] = {"auth": credential, "email": email, }
        self._shred()
        return self._write_all(auths)

    def delete(self, url):
        """Delete credential from keystore for given url"""
        exit_status = 0
        self._verify_keystore()
        auths = self._read_all()
        try:
            del auths[url]
        except KeyError:
            exit_status = 1
            return exit_status
        self._shred()
        exit_status = self._write_all(auths)
        return exit_status

    def erase(self):
        """Delete all credentials from keystore"""
        exit_status = 0
        self._verify_keystore()
        try:
            self._shred()
            os.unlink(self.keystore_file)
        except (IOError, OSError):
            exit_status = 1
            return exit_status
        return exit_status

    def _verify_keystore(self):
        """Verify the keystore file and directory"""
        keystore_uid = FileUtil(self.conf, self.keystore_file).uid()
        if keystore_uid != -1 and keystore_uid != self.conf['uid']:
            raise IOError("not owner of keystore: %s" % self.keystore_file)
        keystore_dir = os.path.dirname(self.keystore_file)
        if FileUtil(self.conf, keystore_dir).uid() != self.conf['uid']:
            raise IOError("keystore dir not found or not owner: %s" %
                          keystore_dir)
        if (keystore_uid != -1 and
                (os.stat(self.keystore_file).st_mode & 0o077)):
            raise IOError("keystore is accessible to group or others: %s" %
                          self.keystore_file)

    def _read_all(self):
        """Read all credentials from file"""
        try:
            with open(self.keystore_file, "r") as filep:
                return json.load(filep)
        except (IOError, OSError, ValueError):
            return dict()

    def _shred(self):
        """Shred file content"""
        exit_status = 0
        self._verify_keystore()
        try:
            size = FileUtil(self.conf, self.keystore_file).size()
            with open(self.keystore_file, "rb+") as filep:
                filep.write(" " * size)
        except (IOError, OSError):
            exit_status = 1
            return exit_status
        return exit_status

    def _write_all(self, auths):
        """Write all credentials to file"""
        exit_status = 0
        self._verify_keystore()
        oldmask = None
        try:
            oldmask = os.umask(0o77)
            with open(self.keystore_file, "w") as filep:
                json.dump(auths, filep)
            os.umask(oldmask)
        except (IOError, OSError):
            if oldmask is not None:
                os.umask(oldmask)
            exit_status = 1
            return exit_status
        return exit_status