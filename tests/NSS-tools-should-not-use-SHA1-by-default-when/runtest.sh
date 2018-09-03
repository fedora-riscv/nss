#!/bin/bash
# vim: dict+=/usr/share/beakerlib/dictionary.vim cpt=.,w,b,u,t,i,k
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   runtest.sh of NSS-tools-should-not-use-SHA1-by-default-when
#   Description: NSS tools should not use SHA1 by default when
#   Author: Hubert Kario <hkario@redhat.com>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Copyright (c) 2016 Red Hat, Inc.
#
#   This copyrighted material is made available to anyone wishing
#   to use, modify, copy, or redistribute it subject to the terms
#   and conditions of the GNU General Public License version 2.
#
#   This program is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE. See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public
#   License along with this program; if not, write to the Free
#   Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#   Boston, MA 02110-1301, USA.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Include Beaker environment
. /usr/share/beakerlib/beakerlib.sh || exit 1

PACKAGE="nss"
PACKAGES="nss openssl"
DBDIR="nssdb"

rlJournalStart
    rlPhaseStartSetup
        rlAssertRpm --all
        rlRun "TmpDir=\$(mktemp -d)" 0 "Creating tmp directory"
        rlRun "pushd $TmpDir"
        rlRun "mkdir nssdb"
        rlRun "certutil -N -d $DBDIR --empty-password"
        rlLogInfo "Create a JAR file"
        rlRun "mkdir java-dir"
        rlRun "pushd java-dir"
        rlRun "mkdir META-INF mypackage"
        rlRun "echo 'Main-Class: mypackage/MyMainFile' > META-INF/MANIFEST.MF"
        rlRun "echo 'Those are not the droids you are looking for' > mypackage/MyMainFile.class"
        #rlRun "jar -cfe package.jar mypackage/MyMainFile mypackage/MyMainFile.class"
        rlRun "popd"
        #rlRun "mv java-dir/package.jar ."
    rlPhaseEnd

    rlPhaseStartTest "Self signing certificates"
        rlRun "dd if=/dev/urandom of=noise bs=1 count=32 >/dev/null"
        rlRun "certutil -d $DBDIR -S -n 'CA' -t 'cTC,cTC,cTC' -s 'CN=CA' -x -z noise"
        rlRun -s "certutil -d $DBDIR -L -n 'CA' -a | openssl x509 -noout -text"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" "$rlRun_LOG"
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
    rlPhaseEnd

    rlPhaseStartTest "Signing certificates"
        rlRun "dd if=/dev/urandom of=noise bs=1 count=32 >/dev/null"
        rlRun "certutil -d $DBDIR -S -n 'server' -t 'u,u,u' -s 'CN=server.example.com' -c 'CA' -z noise --nsCertType sslClient,sslServer,objectSigning,smime"
        rlRun -s "certutil -d $DBDIR -L -n 'server' -a | openssl x509 -noout -text"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" "$rlRun_LOG"
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
    rlPhaseEnd

    rlPhaseStartTest "Certificate request"
        rlRun "dd if=/dev/urandom of=noise bs=1 count=32 >/dev/null"
        rlRun "mkdir srv2db"
        rlRun "certutil -d srv2db -N --empty-password"
        rlRun "certutil -d srv2db -R -s CN=www.example.com -o srv2.req -a -z noise"
        rlRun -s "openssl req -noout -text -in srv2.req"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" "$rlRun_LOG"
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
        rlRun "certutil -d $DBDIR -C -c 'CA' -i srv2.req -a -o srv2.crt"
        rlRun -s "openssl x509 -in srv2.crt -noout -text"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" "$rlRun_LOG"
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
        rlRun "rm -rf srv2db"
    rlPhaseEnd

    rlPhaseStartTest "Certificate request with SHA1"
        rlRun "dd if=/dev/urandom of=noise bs=1 count=32 >/dev/null"
        rlRun "mkdir srv2db"
        rlRun "certutil -d srv2db -N --empty-password"
        rlRun "certutil -d srv2db -R -s CN=www.example.com -o srv2.req -a -z noise -Z SHA1"
        rlRun -s "openssl req -noout -text -in srv2.req"
        rlAssertGrep "Signature Algorithm: sha1WithRSAEncryption" "$rlRun_LOG"
        rlRun "certutil -d $DBDIR -C -c 'CA' -i srv2.req -a -o srv2.crt"
        rlRun -s "openssl x509 -in srv2.crt -noout -text"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" "$rlRun_LOG"
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
        rlRun "rm -rf srv2db"
    rlPhaseEnd

    rlPhaseStartTest "Signing CMS messages"
        rlRun "echo 'This is a document' > document.txt"
        rlRun "cmsutil -S -d $DBDIR -N 'server' -i document.txt -o document.cms"
        rlRun -s "openssl cms -in document.cms -inform der -noout -cmsout -print"
        rlAssertGrep "algorithm: sha256" $rlRun_LOG
        rlAssertNotGrep "algorithm: sha1" $rlRun_LOG
    rlPhaseEnd

    rlPhaseStartTest "CRL signing"
        rlRun "echo $(date --utc +update=%Y%m%d%H%M%SZ) > script"
        rlRun "echo $(date -d 'next week' --utc +nextupdate=%Y%m%d%H%M%SZ) >> script"
        rlRun "echo addext crlNumber 0 1245 >>script"
        rlRun "echo addcert 12 $(date -d 'yesterday' --utc +%Y%m%d%H%M%SZ) >>script"
        rlRun "echo addext reasonCode 0 0 >>script"
        rlRun "cat script"
        rlRun "crlutil -G -c script -d $DBDIR -n CA -o ca.crl"
        rlRun -s "openssl crl -in ca.crl -inform der -noout -text"
        rlAssertGrep "Signature Algorithm: sha256WithRSAEncryption" $rlRun_LOG
        rlAssertNotGrep "Signature Algorithm: sha1WithRSAEncryption" $rlRun_LOG
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun "popd"
        rlRun "rm -r $TmpDir" 0 "Removing tmp directory"
    rlPhaseEnd
rlJournalPrintText
rlJournalEnd
