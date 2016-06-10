#!/usr/bin/env python
#
# Copyright (c) 2016, The Linux Foundation.
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

import pexpect
import sys
import shutil
import os

PROMPT = 'test-branch@data >'

srcdir = os.environ['SRCDIR']
datadir = os.environ['DATADIR']

class GitStub():
    def __init__(self):
        gitdir = os.path.join(datadir, 'git')
        srcgitdir = os.path.join(srcdir, '..', 'stubs', 'data', 'git')

        # create fake git repo
        shutil.copytree(srcgitdir, gitdir)
        os.environ['STUB_GIT_DATADIR'] = gitdir

    def cleanup(self):
        # FIXME: implement
        pass

class SmtpdStub():
    def __init__(self):
        self.smtpddir = os.path.join(datadir, 'smtpd')

        # setup directory for smtpd
        os.mkdir(self.smtpddir)
        os.environ['STUB_SMTPD_DATADIR'] = self.smtpddir

    def get_mails(self):
        mails = []

        for filename in os.listdir(self.smtpddir):
            f = open(os.path.join(self.smtpddir, filename), 'r')
            mails.append(f.read())
            f.close()

        return mails

    def get_mails_as_string(self):
        result = ''
        sep = '----------------------------------------------------------------------'
        i = 0

        for mail in self.get_mails():
            result += 'mail %d:\n%s\n%s%s\n' % (i, sep, mail, sep)
            i += 1

        return result

    def cleanup(self):
        shutil.rmtree(self.smtpddir)
        
class PatchworkStub():
    def __init__(self):
        self.patchesdir = os.path.join(datadir, 'patches')
        srcpatchesdir = os.path.join(srcdir, '..', 'stubs', 'data', 'patches')

        # create copy of patches
        shutil.copytree(srcpatchesdir, self.patchesdir)
        os.environ['STUB_PATCHWORK_DATADIR'] = self.patchesdir

    def cleanup(self):
        shutil.rmtree(self.patchesdir)

class PwcliStubSpawn(pexpect.spawn):
    def __init__(self):
        # use short timeout so that failures don't take too long to detect
        super(PwcliStubSpawn, self).__init__('./run_stub', timeout=3,
                                             logfile=sys.stdout)

    def expect_prompt(self):
        return super(PwcliStubSpawn, self).expect(PROMPT)
        
