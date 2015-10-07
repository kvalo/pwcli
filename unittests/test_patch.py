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
import mock
import email

import pwcli

FAKE_ATTRIBUTES = {
    'name' : 'nnnn',
    'id' : '11',
    'delegate' : 'dddd',
    'state_id' : '1234',
    'state' : 'ssss'
}

TEST_MBOX = 'Content-Type: text/plain; charset="utf-8"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: [1/7] foo\nFrom: Dino Dinosaurus <dino@example.com>\nX-Patchwork-Id: 12345\nMessage-Id: <11111@example.com>\nTo: list@example.com\nDate: Thu,  10 Feb 2011 15:23:31 +0300\n\nFoo commit log. Ignore this text\n\nSigned-off-by: Dino Dinosaurus <dino@example.com>\n\n---\nFIXME: add the patch here\n'

class TestGit(unittest.TestCase):
    @mock.patch('pwcli.PWCLI')
    def test_attributes(self, pw):
        attributes = FAKE_ATTRIBUTES
        patch = pwcli.Patch(pw, attributes, False)

        self.assertEqual(patch.get_name(), attributes['name'])
        self.assertEqual(patch.get_id(), attributes['id'])
        self.assertEqual(patch.get_delegate(), attributes['delegate'])
        self.assertEqual(patch.get_state_id(), attributes['state_id'])
        self.assertEqual(patch.get_state_name(), attributes['state'])

        pw.get_state_id = mock.Mock(return_value='7777')
        patch.set_state_name('Accepted')
        self.assertEqual(patch.get_state_name(), 'Accepted')
        self.assertEqual(patch.get_state_id(), '7777')
        pw.rpc.patch_set.assert_called_with(attributes['id'], { 'state' : '7777'})

    def test_reply_msg(self):
        attributes = FAKE_ATTRIBUTES
        patch = pwcli.Patch(None, attributes, False)

        patch.get_email = mock.Mock(return_value=email.message_from_string(TEST_MBOX))

        reply = patch.get_reply_msg('Timo Testi', 'test@example.com')

        self.assertEqual(reply['From'], 'Timo Testi <test@example.com>')
        self.assertEqual(reply['To'], 'Dino Dinosaurus <dino@example.com>')
        self.assertFalse('Cc' in reply)
        self.assertEqual(reply['Subject'], 'Re: [1/7] foo')

if __name__ == '__main__':
    unittest.main()
