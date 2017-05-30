#!/usr/bin/env python
#
# Copyright (c) 2015, The Linux Foundation.
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

import unittest
import subprocess
import tempfile
import os
import shutil
import logging
import hashlib
import stubslib

from pwcli import Git
from pwcli import GitCommit

class TestGit(unittest.TestCase):

    def dummy_output(self, buf):
        pass

    def setUp(self):
        output = subprocess.check_output(['git', '--version', 'branch'])

        output = output.strip()

        self.datadir = tempfile.mkdtemp(prefix = 'pwcli-unittest-')

        os.environ['STUB_GIT_DATADIR'] = self.datadir

        if output.splitlines()[0] != 'stub-git':
            self.fail('Not using stub-git')
            return

    def tearDown(self):
        shutil.rmtree(self.datadir)

    def test_get_branch(self):
        gitrepo = stubslib.GitRepository.load(self.datadir)

        gitrepo.create_branch('bbb')
        gitrepo.create_branch('foo')
        gitrepo.create_branch('ccc')

        gitrepo.change_branch('foo')

        git = Git(False, self.dummy_output)
        branch = git.get_branch()

        self.assertEqual(branch, 'foo')

    def test_am(self):
        mbox = '''From nobody
From: Ed Example <ed@example.com
Subject: [PATCH] dummy test
Date: Date: Thu,  10 Feb 2011 15:23:31 +0300

foo body
'''
        sha1sum = hashlib.sha1(mbox).hexdigest()

        git = Git(False, self.dummy_output)
        git.am(mbox)

        gitrepo = stubslib.GitRepository.load(self.datadir)
        self.assertEquals(gitrepo.get_commits()[0].mbox, mbox)

    def test_am_dry_run(self):
        mbox = 'dummy mbox file'
        git = Git(True, self.dummy_output)
        git.am(mbox)

        gitrepo = stubslib.GitRepository.load(self.datadir)
        self.assertEquals(len(gitrepo.get_commits()), 0)

class TestGitCommit(unittest.TestCase):

    def test_parse(self):
        f = open('stg-show-1.data')
        commit = GitCommit.parse(f.read())
        f.close()

        self.assertEqual(commit.commit_id,
                         '8bd453fe60574334173cdbb51faa390b98678063')
        self.assertEqual(commit.patchwork_id,
                         12345)

if __name__ == '__main__':
    unittest.main()
