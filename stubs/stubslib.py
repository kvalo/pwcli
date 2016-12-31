# Copyright (c) 2017, The Linux Foundation.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import hashlib
import os
import ConfigParser
import email
import re

class GitCommit():
    def __init__(self, commit_id, mbox):
        self.id = commit_id
        self.abbrev_id = '%.12s' % (self.id)
        self.mbox = mbox

    def get_subject(self):
        msg = email.message_from_string(self.mbox)

        subject = msg['Subject']

        # remove all '[foo]' tags
        subject = re.sub('\[.*\]', '', subject)
        subject = subject.strip()

        return subject

    def get_oneline(self):
        return '%s %s' % (self.abbrev_id, self.get_subject())
        
class GitRepository():
    def __init__(self, gitdir):
        self.gitdir = gitdir
        self.conflict_file = os.path.join(self.gitdir, 'conflict')
        self.objectsdir = os.path.join(self.gitdir, 'objects')
        self.commitsfile = os.path.join(self.objectsdir, 'commits')

        self.config = ConfigParser.RawConfigParser()
        self.config.read(os.path.join(gitdir, 'config'))

        self.head = 'master'

        # a dict where key is name of the branch and value is list of
        # GitCommit objects
        self.branches = {}

        # all commits in a repository, key is commit id as string and
        # value is GitCommit object
        self.commits = {}

        self.load_commits()

    def load_commits(self):
        self.branches[self.head] = []

        # in case the repository is not initialised
        if not os.path.exists(self.commitsfile):
            return

        f = open(self.commitsfile, 'r')
        buf = f.read()
        f.close()

        commit_ids = buf.splitlines()

        for commit_id in commit_ids:
            f = open(os.path.join(self.objectsdir, commit_id), 'r')
            mbox = f.read()
            f.close()

            commit = GitCommit(commit_id, mbox)
            self.commits[commit_id] = commit
            self.branches[self.head].append(commit)

    def get_head_commits(self):
        return self.branches[self.head]

    def get_branches(self):
        f = open(os.path.join(self.gitdir, 'branches'), 'r')
        branches = f.readlines()
        f.close()

        # strip newline from all lines
        result = []
        for branch in branches:
            result.append(branch.strip())

        return result

    def is_conflict_enabled(self):
        return os.path.exists(self.conflict_file)

    def remove_conflict_file(self):
        os.remove(self.conflict_file)

    def add_commit(self, buf):
        if not os.path.isdir(self.objectsdir):
            os.mkdir(self.objectsdir)

        sha1sum = hashlib.sha1(buf).hexdigest()

        f = open(self.commitsfile, 'a')
        f.write(sha1sum + '\n')
        f.close()

        f = open(os.path.join(self.objectsdir, sha1sum), 'w')
        f.write(buf)
        f.close()

    # FIXME: this looks incomplete
    def cherry_pick(self, commit_id):
        if commit_id not in self.commits:
            raise ValueError('Commit %s not found.' % (commit_id))

        f = open(self.commitsfile, 'a')
        f.write(commit_id + '\n')
        f.close()
        
    def get_config(self, section, name):
        if not self.config.has_option(section, name):
            raise ValueError('Config not found')

        return self.config.get(section, name)
        
