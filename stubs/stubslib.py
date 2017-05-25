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
import pickle
import collections

GIT_DB_NAME = 'db.pickle'

class GitCommit():
    def __init__(self, commit_id, mbox, stg_name=None):
        self.id = commit_id
        self.abbrev_id = '%.12s' % (self.id)
        self.mbox = mbox
        self.stg_name = stg_name

        msg = email.message_from_string(mbox)

        subject = msg['Subject']

        # remove all '[foo]' tags
        subject = re.sub('\[.*\]', '', subject)

        self.subject = subject.strip()
        self.author = msg['From']
        self.date = msg['Date']
        self.body = msg.get_payload()

    def get_subject(self):
        return self.subject

    def get_oneline(self):
        return '%s %s' % (self.abbrev_id, self.get_subject())

class GitRepository():
    @staticmethod
    def load(gitdir):
        path = os.path.join(gitdir, GIT_DB_NAME)
        if not os.path.exists(path):
            return GitRepository(gitdir)

        f = open(path, 'r')
        repo = pickle.load(f)
        f.close()

        return repo

    def __init__(self, gitdir):
        self.gitdir = gitdir

        self.config = ConfigParser.RawConfigParser()
        self.config.read(os.path.join(gitdir, 'config'))

        # FIXME: default branch name should be 'master'
        self.head = 'test-branch'

        # a dict where key is name of the branch and value is list of
        # GitCommit objects
        self.branches = {}
        self.branches[self.head] = []

        # TODO: this should per branch, not one for all branches
        self.stg_patches = collections.OrderedDict()

        # all commits in a repository, key is commit id as string and
        # value is GitCommit object
        self.commits = {}

        self.conflict = False

        self.stg_import_failure = 0

    def dump(self):
        path = os.path.join(self.gitdir, GIT_DB_NAME)
        
        f = open(path, 'w')
        pickle.dump(self, f)
        f.close()

    # FIXME: rename get_commits(self, branch='master')
    def get_head_commits(self):
        return self.branches[self.head]

    def get_branches(self):
        # strip newline from all lines
        result = []
        for branch in self.branches:
            if branch == self.head:
                head = '*'
            else:
                head = ' '

            s = '%c %s' % (head, branch.strip())
            result.append(s)

        return result

    def is_conflict_enabled(self):
        return self.conflict

    def enable_conflict(self):
        self.conflict = True
        self.dump()

    def remove_conflict_file(self):
        self.conflict = False
        self.dump()

    def _add_commit(self, commit_id, mbox, stg_name=None):
        commit = GitCommit(commit_id, mbox, stg_name)
        self.commits[commit_id] = commit
        self.branches[self.head].append(commit)

        self.dump()

        return commit

    def add_commit(self, mbox):
        commit_id = hashlib.sha1(mbox).hexdigest()
        return self._add_commit(commit_id, mbox)

    def create_branch(self, branch):
        self.branches[branch] = []
        self.dump()

    def change_branch(self, branch):
        if branch not in self.branches:
            raise ValueError('Branch %s does not exist')

        self.head = branch
        self.dump()

    # FIXME: this looks incomplete
    def cherry_pick(self, commit_id):
        if commit_id not in self.commits:
            raise ValueError('Commit %s not found.' % (commit_id))

        commit = self.commits[commit_id]

        self.branches[self.head].append(commit)
        
    def get_config(self, section, name):
        if not self.config.has_option(section, name):
            raise ValueError('Config not found')

        return self.config.get(section, name)
        
    def import_stg_commit(self, mbox):

        if self.stg_import_failure > 0:
            self.stg_import_failure -= 1
            self.dump()

            if self.stg_import_failure == 0:
                # this import should fail
                raise ValueError('stg_import_failure is set')

        # create stgit name for the patch
        msg = email.message_from_string(mbox)
        patch_name = msg['Subject']
        patch_name = patch_name.lower()

        # remove all tags ("[foo]") before the title
        patch_name = re.sub(r'^\s*(\[.*?\]\s*)*', '', patch_name)

        # replace all non-alphanumeric characters with a hyphen
        patch_name = re.sub(r'\W+', '-', patch_name)

        # FIXME: Check if there's already a patch with that name and in
        # that case append a number suffix patch_name with a number.

        # strip out the date ('From nobody <date>') from the first line,
        # which is added by email.message.Message.as_string(unixfrom=True)
        buf_cleaned = re.sub(r'^From nobody.*\n', 'From nobody\n', mbox)
        commit_id = hashlib.sha1(buf_cleaned).hexdigest()

        commit = self._add_commit(commit_id, mbox, patch_name)
        self.stg_patches[patch_name] = commit

        self.dump()

        return commit

    def delete_stg_top_commit(self):
        # remote the last item from the dict
        self.stg_patches.popitem()
        self.branches[self.head].pop()
        self.dump()

    # An integer which patch import should fail (3 = the third import
    # fails)
    def set_stg_import_failure(self, val):
        self.stg_import_failure = val

        self.dump()
