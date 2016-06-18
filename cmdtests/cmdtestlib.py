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
import subprocess
import time
import logging

# logging
logging.basicConfig()
logger = logging.getLogger('cmdtestlib')

# uncomment to get debug logs
#logger.setLevel(logging.DEBUG)

PROMPT = 'test-branch@data >'
PROMPT_REVIEW_STATE = 'Under review/Changes requested/Deferred/Rejected/aBort?'
PROMPT_COMMIT_ALL = 'commit All/commit Individually/aBort\?'
PROMPT_COMMIT_ACCEPT = 'Accept/request Changes/Reject/Show mail/Edit mail/aBort?'

# the toplevel source directory
srcdir = os.environ['SRCDIR']

# the directory where the tests can store temporary data
testdatadir = os.environ['DATADIR']

stubsdir = os.path.join(srcdir, 'stubs')

sys.path.insert(0, stubsdir)
import stubs

logger.debug('srcdir=%r' % (srcdir))
logger.debug('testdatadir=%r' % (testdatadir))
logger.debug('stubsdir=%r' % (stubsdir))

class StubContext():
    def __init__(self, start=False):
        self.git = stubs.GitStub()
        self.smtpd = stubs.SmtpdStub()
        self.patchwork = stubs.PatchworkStub()
        self.pwcli = None

        # move to the fake git repository before starting pwcli
        os.chdir(testdatadir)

        if start:
            self.start()

    def start(self):
        try:
            self.git.start()
            self.smtpd.start()
            self.patchwork.start()

            # must be instiated only after daemon stubs are running,
            # as this immediately starts pwcli
            self.pwcli = PwcliSpawn()
        except Exception as e:
            print 'Failed to start stubs: %s' % (e)
            self.stop_and_cleanup()
            sys.exit(1)

    def stop(self):
        self.git.stop()
        self.smtpd.stop()
        self.patchwork.stop()

    def cleanup(self):
        self.git.cleanup()
        self.smtpd.cleanup()
        self.patchwork.cleanup()

    def stop_and_cleanup(self):
        self.stop()
        self.cleanup()

class PwcliSpawn(pexpect.spawn):
    def __init__(self):
        # use short timeout so that failures don't take too long to detect
        super(PwcliSpawn, self).__init__(os.path.join(srcdir, 'pwcli'),
                                         timeout=3,
                                         logfile=sys.stdout)

    def expect_prompt(self):
        return super(PwcliSpawn, self).expect(PROMPT)

class PwcliStubSpawn(pexpect.spawn):
    def __init__(self):
        # use short timeout so that failures don't take too long to detect
        super(PwcliStubSpawn, self).__init__('./run_stub', timeout=3,
                                             logfile=sys.stdout)

    def expect_prompt(self):
        return super(PwcliStubSpawn, self).expect(PROMPT)
        
