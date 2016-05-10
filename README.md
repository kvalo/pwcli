# pwcli - a script for applying patches from patchwork and sending summary emails

## Introduction

pwcli is script which I wrote to ease my kernel maintainer duties. It
provides a simple readline interface for accessing patches in a
patchwork servers over the XML-RPC interface, uses git to commit the
patches to a local repository and send emails using an SMTP server.
The benefit from the script is that it doesn't matter if you apply one
or hundred patches, it's still the same amount of work for you (unless
there are conflicts, of course).

This still a crude prototype but it already helps me to avoid tedious
manual work. All feedback very welcome:

Kalle Valo <kvalo@codeaurora.org>

## Screenshots

```$ pwcli
Connecting to https://patchwork.kernel.org/xmlrpc/
User          : kvalo (7477, 30052, 118371)
Projects      : linux-wireless
Tree          : wireless-drivers-next
Branch        : master
New           : 36
Review        : 3
Upstream      : 0
Deferred      : 13
Total         : 52
master@wireless-drivers-next > list review
[  1] 8927801 [v2,7/7] wil6210: add support for device led configuration
[  2] 8939281 mwifiex: change sleep cookie poll count
[  3] 8993841 [v2] rtlwifi: Fix logic error in enter/exit power-save mode
master@wireless-drivers-next > commit 2
Retrieving patches (1/1) 
8939281 mwifiex: change sleep cookie poll count
------------------------------------------------------------
1 patches
commit All/commit Individually/aBort? a
Applying: mwifiex: change sleep cookie poll count
============================================================
1 patches applied:

522a38e7a652 mwifiex: change sleep cookie poll count

Accept/request Changes/Reject/Show mail/Edit mail/aBort? 
```

## Installation

pwcli requires patchwork 2.7 (maybe older versions also work but I
haven't tested myself). To install it just to copy the pwcli script
somewhere in your $PATH:

cp pwcli /usr/local/bin/

It needs a configuration file in .git/pwcli/config:

```[general]
url = https://patchwork.example.com/xmlrpc/
username = edward
password = 0987654321
project = acme-devel
```

For emails pwcli uses some of git configuration variables, so you want to make sure they are correctly set:

```git config user.name 'Edward Example'
git config user.email 'edward@example.com'
git config sendemail.smtpserver smtp.example.com
git config sendemail.smtpserverport 587
git config sendemail.smtpuser edward
git config sendemail.smtppass 1234567890
git config sendemail.smtpencryption tls
```

## Tests

I wrote various tests for the script, use run_tests.sh to run them
all. These are currently run on Ubuntu 12.04 with these packages (the
list might not be complete):

```ii  cmdtest              0.15-1.1             blackbox testing of Unix command line programs
ii  python-mock          0.7.2-1              Mocking and Testing Library
ii  python-pexpect       2.3-1ubuntu2         Python module for automating interactive applications
```

## Contributing patches

If you want to send patches please read CONTRIBUTIONS file.