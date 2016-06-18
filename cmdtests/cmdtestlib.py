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

cmdtestdir = os.environ['SRCDIR']
testdatadir = os.environ['DATADIR']
srcdir = os.path.abspath(os.path.join(cmdtestdir, '..'))
stubsdir = os.path.join(srcdir, 'stubs')

logger.debug('srcdir=%r' % (srcdir))
logger.debug('testdatadir=%r' % (testdatadir))
logger.debug('cmdtestdir=%r' % (cmdtestdir))
logger.debug('stubsdir=%r' % (stubsdir))

class StubContext():
    def __init__(self, start=False):
        self.git = GitStub()
        self.smtpd = SmtpdStub()
        self.patchwork = PatchworkStub()

        # move to the fake git repository before starting pwcli
        os.chdir(testdatadir)

        self.pwcli = PwcliSpawn()

        if start:
            self.start()

    def start(self):
        try:
            self.git.start()
            self.smtpd.start()
            self.patchwork.start()
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

class GitStub():
    def __init__(self):
        self.gitdir = os.path.join(testdatadir, 'git')
        srcgitdir = os.path.join(stubsdir, 'data', 'git')

        logger.debug('GitStub(): gitdir=%r' % (self.gitdir))

        # create fake git repo
        shutil.copytree(srcgitdir, self.gitdir)
        os.environ['STUB_GIT_DATADIR'] = self.gitdir

        os.environ['GIT_DIR'] = 'git'
        os.environ['PATH'] = '%s:%s' % ((stubsdir), os.environ['PATH'])

        self.started = False

    def start(self):
        logger.debug('GitStub.start(): %s' % (os.getcwd()))
        p = subprocess.Popen(['git', '--version', 'branch'], stdout=subprocess.PIPE)
        (stdout, stderr) = p.communicate()

        git_version = stdout.splitlines()[0]

        if git_version != 'stub-git':
            raise Exception('Not running git-stub: %s' % git_version)

        self.started = True

    def stop(self):
        if not self.started:
            return

        self.started = False

    def cleanup(self):
        shutil.rmtree(self.gitdir)

class SmtpdStub():
    SMTP_PORT = 5870

    def __init__(self):
        self.smtpddir = os.path.join(testdatadir, 'smtpd')

        # setup directory for smtpd
        os.mkdir(self.smtpddir)
        os.environ['STUB_SMTPD_DATADIR'] = self.smtpddir

        logger.debug('SmtpdStub(): smtpddir=%r' % (self.smtpddir))

        self.started = False

    def start(self):
        # Note: there's a problem that stdout from smtpd output does
        # not go to cmdtest stdout log anymore (after switching away
        # from using the run_stub script). I do not know why it is
        # exactly, maybe something to do how Popen() inherits stdout
        # rules from the running process?
        self.smtpd = subprocess.Popen([os.path.join(stubsdir, 'smtpd'),
                                       '--port=%d' % SmtpdStub.SMTP_PORT])

        # wait some time to make sure that the stub started
        time.sleep(0.2)

        if self.smtpd.poll() != None:
            raise Exception('Failed to start smtpd stub: %d' % self.smtpd.returncode)

        self.started = True

    def stop(self):
        if not self.started:
            return

        self.smtpd.terminate()
        self.smtpd.wait()

        self.started = False

    def cleanup(self):
        shutil.rmtree(self.smtpddir)

    def get_mails(self):
        mails = []

        mailfiles = os.listdir(self.smtpddir)
        logger.debug('SmtpdStub(): mailfiles=%r' % (mailfiles))

        for filename in mailfiles:
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

class PatchworkStub():
    def __init__(self):
        self.patchesdir = os.path.join(testdatadir, 'patches')
        srcpatchesdir = os.path.join(stubsdir, 'data', 'patches')

        # create copy of patches
        shutil.copytree(srcpatchesdir, self.patchesdir)
        os.environ['STUB_PATCHWORK_DATADIR'] = self.patchesdir

        logger.debug('PatchworkStub(): patchesdir=%r' % (self.patchesdir))

        self.started = False

    def start(self):
        self.patchwork = subprocess.Popen([os.path.join(stubsdir, 'patchwork')])

        # wait some time to make sure that the stub started
        time.sleep(0.2)

        if self.patchwork.poll() != None:
            raise Exception('Failed to start patchwork stub: %d' % self.patchwork.returncode)

        self.started = True

    def stop(self):
        if not self.started:
            return

        self.patchwork.terminate()
        self.patchwork.wait()

        self.started = False

    def cleanup(self):
        shutil.rmtree(self.patchesdir)

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
        
