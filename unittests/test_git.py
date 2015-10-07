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

from pwcli import Git

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
        if True:
            shutil.rmtree(self.datadir)
        else:
            print self.datadir

    def test_get_branch(self):
        f = open(os.path.join(self.datadir, 'stub-git-branches'), 'w')
        f.write('  aaa\n')
        f.write('  bbb\n')
        f.write('* foo\n')
        f.write('  ccc\n')
        f.close()

        git = Git(False, self.dummy_output)
        branch = git.get_branch()

        self.assertEqual(branch, 'foo')

    def test_am(self):
        mbox = 'dummy mbox file'
        git = Git(False, self.dummy_output)
        git.am(mbox)

        f = open(os.path.join(self.datadir, 'stub-git-am-s'), 'r')
        self.assertEquals(f.read(), mbox)
        f.close()

    def test_am_dry_run(self):
        mbox = 'dummy mbox file'
        git = Git(True, self.dummy_output)
        git.am(mbox)

        self.assertFalse(os.path.exists(os.path.join(self.datadir, 'stub-git-am-s')))

if __name__ == '__main__':
    unittest.main()
