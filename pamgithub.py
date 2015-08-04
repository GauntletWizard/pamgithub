#!/bin/env python
#
# PamGithub is a module to take a Github user name and add it's public SSH keys to an authorized_keys file,
# Effectively and securely granting access to that user.

import gflags
import sys
import urllib2
from os.path import expanduser

FLAGS = gflags.FLAGS

gflags.DEFINE_string('authorized_keyfile', '~/.ssh/authorized_keys', 'File containing pre-existing authorizations to merge. Set to blank to ignore existing authroized keys.')
gflags.DEFINE_list('id_files', ['~/.ssh/id_rsa.pub', '~/.ssh/id_dsa.pub'], 'Files containing keys to unmerge')
GITHUB = "https://github.com/%s.keys"

class Keyfile:
	def __init__(self, f):
		if type(f) == str:
			try:
				self._load(open(expanduser(f)))
			except Exception:
				self._keys = frozenset()
				return
		elif type(f) in [set, frozenset]:
			self._keys = frozenset(f)
		else:
			self._load(f)

	def _load(self, f):
		keys = []
		for line in f:
			key = SSHKey(line)
			keys.append(key)
		self._keys = frozenset(keys)

	def merge(self, other):
		return Keyfile(self._keys.union(other._keys))

	def remove(self, other):
		return Keyfile(self._keys.difference(other._keys))
	
	def __repr__(self):
		print self._keys
		return "\n".join(map(str, self._keys))


class SSHKey:
	''' SSHKey implements an abstraction of a ssh public key.

	Two SSHKeys are equal if their cypher and key are equal, irrespective of 
	their comment. '''
	def __init__(self, line):
		parts = line.split()
		if len(parts) >= 2:
			self._cypher = parts[0]
			self._key = parts[1]
		if len(parts) == 3:
			self._comment = parts[2]
		else:
			self._comment = "git@github.com"

	def __repr__(self):
		return " ".join([self._cypher, self._key, self._comment])

	def __eq__(self, other):
		return self._key == other._key and self._cypher == other._cypher
	
	def __hash__(self):
		return hash(" ".join([self._cypher, self._key]))
	
	def __str__(self):
		return self.__repr__()

def main():
	argv = FLAGS(sys.argv)
	if len(argv) != 2:
		print "Usage: pamgithub [options] GITHUB_USERNAME"
		return
	if FLAGS.authorized_keyfile:
		keys = Keyfile(FLAGS.authorized_keyfile)
	else:
		keys = Keyfile(frozenset())
	for f in FLAGS.id_files:
		try:
			keys = keys.remove(Keyfile(f))
		except Exception:
			pass
	gitkeys = Keyfile(urllib2.urlopen(GITHUB % argv[1]))
	print len(gitkeys._keys)
	keys = keys.merge(gitkeys)
	print keys
	
if __name__ == '__main__':
	main()
