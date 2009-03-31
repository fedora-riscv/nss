%define nspr_version 4.7
%define unsupported_tools_directory %{_libdir}/nss/unsupported-tools

Summary:          Network Security Services
Name:             nss
Version:          3.12.2.99.3
Release:          3%{?dist}
License:          MPLv1.1 or GPLv2+ or LGPLv2+
URL:              http://www.mozilla.org/projects/security/pki/nss/
Group:            System Environment/Libraries
Requires:         nspr >= %{nspr_version}
Requires:         sqlite
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:    nspr-devel >= %{nspr_version}
BuildRequires:    sqlite-devel
BuildRequires:    zlib-devel
BuildRequires:    pkgconfig
BuildRequires:    gawk
BuildRequires:    psmisc
BuildRequires:    perl

Source0:          %{name}-%{version}-stripped.tar.bz2

Source1:          nss.pc.in
Source2:          nss-config.in
Source3:          blank-cert8.db
Source4:          blank-key3.db
Source5:          blank-secmod.db
Source8:          nss-prelink.conf
Source12:         %{name}-pem-20080124.tar.bz2

Patch1:           nss-no-rpath.patch
Patch2:           nss-nolocalsql.patch
Patch4:           nss-pem-bug483855.patch
Patch5:           nss-pem-bug429175.patch
Patch6:           nss-enable-pem.patch

%description
Network Security Services (NSS) is a set of libraries designed to
support cross-platform development of security-enabled client and
server applications. Applications built with NSS can support SSL v2
and v3, TLS, PKCS #5, PKCS #7, PKCS #11, PKCS #12, S/MIME, X.509
v3 certificates, and other security standards.


%package tools
Summary:          Tools for the Network Security Services
Group:            System Environment/Base
Requires:         nss = %{version}-%{release}
Requires:         zlib

%description tools
Network Security Services (NSS) is a set of libraries designed to
support cross-platform development of security-enabled client and
server applications. Applications built with NSS can support SSL v2
and v3, TLS, PKCS #5, PKCS #7, PKCS #11, PKCS #12, S/MIME, X.509
v3 certificates, and other security standards.

Install the nss-tools package if you need command-line tools to
manipulate the NSS certificate and key database.


%package devel
Summary:          Development libraries for Network Security Services
Group:            Development/Libraries
Requires:         nss = %{version}-%{release}
Requires:         nspr-devel >= %{nspr_version}
Requires:         pkgconfig

%description devel
Header and Library files for doing development with Network Security Services.


%package pkcs11-devel
Summary:          Development libraries for PKCS #11 (Cryptoki) using NSS
Group:            Development/Libraries
Requires:         nss-devel = %{version}-%{release}

%description pkcs11-devel
Library files for developing PKCS #11 modules using basic NSS 
low level services.


%prep
%setup -q
%setup -q -T -D -n %{name}-%{version} -a 12

%patch1 -p0
%patch2 -p0
%patch4 -p0 -b .483855
%patch5 -p0 -b .429175
%patch6 -p0 -b .libpem


%build

FREEBL_NO_DEPEND=1
export FREEBL_NO_DEPEND

# Enable compiler optimizations and disable debugging code
BUILD_OPT=1
export BUILD_OPT

# Generate symbolic info for debuggers
XCFLAGS=$RPM_OPT_FLAGS
export XCFLAGS

#export NSPR_INCLUDE_DIR=`nspr-config --includedir`
#export NSPR_LIB_DIR=`nspr-config --libdir`

PKG_CONFIG_ALLOW_SYSTEM_LIBS=1
PKG_CONFIG_ALLOW_SYSTEM_CFLAGS=1

export PKG_CONFIG_ALLOW_SYSTEM_LIBS
export PKG_CONFIG_ALLOW_SYSTEM_CFLAGS

NSPR_INCLUDE_DIR=`/usr/bin/pkg-config --cflags-only-I nspr | sed 's/-I//'`
NSPR_LIB_DIR=`/usr/bin/pkg-config --libs-only-L nspr | sed 's/-L//'`

export NSPR_INCLUDE_DIR
export NSPR_LIB_DIR

%ifarch x86_64 ppc64 ia64 s390x sparc64
USE_64=1
export USE_64
%endif

# NSS_ENABLE_ECC=1
# export NSS_ENABLE_ECC

%{__make} -C ./mozilla/security/coreconf
%{__make} -C ./mozilla/security/dbm
%{__make} -C ./mozilla/security/nss

# Set up our package file
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}/pkgconfig
%{__cat} %{SOURCE1} | sed -e "s,%%libdir%%,%{_libdir},g" \
                          -e "s,%%prefix%%,%{_prefix},g" \
                          -e "s,%%exec_prefix%%,%{_prefix},g" \
                          -e "s,%%includedir%%,%{_includedir}/nss3,g" \
                          -e "s,%%NSPR_VERSION%%,%{nspr_version},g" \
                          -e "s,%%NSS_VERSION%%,%{version},g" > \
                          $RPM_BUILD_ROOT/%{_libdir}/pkgconfig/nss.pc

NSS_VMAJOR=`cat mozilla/security/nss/lib/nss/nss.h | grep "#define.*NSS_VMAJOR" | awk '{print $3}'`
NSS_VMINOR=`cat mozilla/security/nss/lib/nss/nss.h | grep "#define.*NSS_VMINOR" | awk '{print $3}'`
NSS_VPATCH=`cat mozilla/security/nss/lib/nss/nss.h | grep "#define.*NSS_VPATCH" | awk '{print $3}'`

export NSS_VMAJOR 
export NSS_VMINOR 
export NSS_VPATCH

%{__mkdir_p} $RPM_BUILD_ROOT/%{_bindir}
%{__cat} %{SOURCE2} | sed -e "s,@libdir@,%{_libdir},g" \
                          -e "s,@prefix@,%{_prefix},g" \
                          -e "s,@exec_prefix@,%{_prefix},g" \
                          -e "s,@includedir@,%{_includedir}/nss3,g" \
                          -e "s,@MOD_MAJOR_VERSION@,$NSS_VMAJOR,g" \
                          -e "s,@MOD_MINOR_VERSION@,$NSS_VMINOR,g" \
                          -e "s,@MOD_PATCH_VERSION@,$NSS_VPATCH,g" \
                          > $RPM_BUILD_ROOT/%{_bindir}/nss-config

chmod 755 $RPM_BUILD_ROOT/%{_bindir}/nss-config

# enable the following line to force a test failure
# find ./mozilla -name \*.chk | xargs rm -f

# Run test suite.
# In order to support multiple concurrent executions of the test suite
# (caused by concurrent RPM builds) on a single host,
# we'll use a random port. Also, we want to clean up any stuck
# selfserv processes. If process name "selfserv" is used everywhere,
# we can't simply do a "killall selfserv", because it could disturb
# concurrent builds. Therefore we'll do a search and replace and use
# a different process name.
# Using xargs doesn't mix well with spaces in filenames, in order to
# avoid weird quoting we'll require that no spaces are being used.

SPACEISBAD=`find ./mozilla/security/nss/tests | grep -c ' '` ||:
if [ SPACEISBAD -ne 0 ]; then
  echo "error: filenames containing space are not supported (xargs)"
  exit 1
fi
MYRAND=`perl -e 'print 9000 + int rand 1000'`; echo $MYRAND ||:
RANDSERV=selfserv_${MYRAND}; echo $RANDSERV ||:
DISTBINDIR=`ls -d ./mozilla/dist/*.OBJ/bin`; echo $DISTBINDIR ||:
pushd `pwd`
cd $DISTBINDIR
ln -s selfserv $RANDSERV
popd
# man perlrun, man perlrequick
# replace word-occurrences of selfserv with selfserv_$MYRAND
find ./mozilla/security/nss/tests -type f |\
  grep -v "\.db$" |grep -v "\.crl$" | grep -v "\.crt$" |\
  grep -vw CVS  |xargs grep -lw selfserv |\
  xargs -l perl -pi -e "s/\bselfserv\b/$RANDSERV/g" ||:

killall $RANDSERV || :

rm -rf ./mozilla/tests_results
cd ./mozilla/security/nss/tests/
# all.sh is the test suite script
HOST=localhost DOMSUF=localdomain PORT=$MYRAND ./all.sh
cd ../../../../

killall $RANDSERV || :

TEST_FAILURES=`grep -c FAILED ./mozilla/tests_results/security/localhost.1/output.log` || :
if [ $TEST_FAILURES -ne 0 ]; then
  echo "error: test suite returned failure(s)"
  exit 1
fi
echo "test suite completed"


%install

# There is no make install target so we'll do it ourselves.

%{__mkdir_p} $RPM_BUILD_ROOT/%{_includedir}/nss3
%{__mkdir_p} $RPM_BUILD_ROOT/%{_bindir}
%{__mkdir_p} $RPM_BUILD_ROOT/%{_lib}
%{__mkdir_p} $RPM_BUILD_ROOT/%{unsupported_tools_directory}

# Copy the binary libraries we want
for file in libsoftokn3.so libfreebl3.so libnss3.so libnssutil3.so \
            libssl3.so libsmime3.so libnssckbi.so libnsspem.so libnssdbm3.so
do
  %{__install} -m 755 mozilla/dist/*.OBJ/lib/$file $RPM_BUILD_ROOT/%{_lib}
  ln -sf ../../%{_lib}/$file $RPM_BUILD_ROOT/%{_libdir}/$file
done

# These ghost files will be generated in the post step
# Make sure chk files can be found in both places
for file in libsoftokn3.chk libfreebl3.chk
do
  touch $RPM_BUILD_ROOT/%{_lib}/$file
  ln -s ../../%{_lib}/$file $RPM_BUILD_ROOT/%{_libdir}/$file
done

# Install the empty NSS db files
%{__mkdir_p} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb
%{__install} -m 644 %{SOURCE3} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/cert8.db
%{__install} -m 644 %{SOURCE4} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/key3.db
%{__install} -m 644 %{SOURCE5} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/secmod.db
%{__mkdir_p} $RPM_BUILD_ROOT/%{_sysconfdir}/prelink.conf.d
%{__install} -m 644 %{SOURCE8} $RPM_BUILD_ROOT/%{_sysconfdir}/prelink.conf.d/nss-prelink.conf

# Copy the development libraries we want
for file in libcrmf.a libnssb.a libnssckfw.a
do
  %{__install} -m 644 mozilla/dist/*.OBJ/lib/$file $RPM_BUILD_ROOT/%{_libdir}
done

# Copy the binaries we want
for file in certutil cmsutil crlutil modutil pk12util signtool signver ssltap
do
  %{__install} -m 755 mozilla/dist/*.OBJ/bin/$file $RPM_BUILD_ROOT/%{_bindir}
done

# Copy the binaries we ship as unsupported
for file in atob btoa derdump ocspclnt pp selfserv shlibsign strsclnt symkeyutil tstclnt vfyserv vfychain
do
  %{__install} -m 755 mozilla/dist/*.OBJ/bin/$file $RPM_BUILD_ROOT/%{unsupported_tools_directory}
done

# Copy the include files we want
for file in mozilla/dist/public/nss/*.h
do
  %{__install} -m 644 $file $RPM_BUILD_ROOT/%{_includedir}/nss3
done


%clean
%{__rm} -rf $RPM_BUILD_ROOT


%post
/sbin/ldconfig >/dev/null 2>/dev/null
%{unsupported_tools_directory}/shlibsign -i /%{_lib}/libsoftokn3.so >/dev/null 2>/dev/null
%{unsupported_tools_directory}/shlibsign -i /%{_lib}/libfreebl3.so >/dev/null 2>/dev/null


%postun
/sbin/ldconfig >/dev/null 2>/dev/null


%files
%defattr(-,root,root)
/%{_lib}/libnss3.so
/%{_lib}/libnssutil3.so
/%{_lib}/libnssdbm3.so
/%{_lib}/libssl3.so
/%{_lib}/libsmime3.so
/%{_lib}/libsoftokn3.so
/%{_lib}/libnssckbi.so
/%{_lib}/libnsspem.so
/%{_lib}/libfreebl3.so
%{unsupported_tools_directory}/shlibsign
%ghost /%{_lib}/libsoftokn3.chk
%ghost /%{_lib}/libfreebl3.chk
%dir %{_libdir}/nss
%dir %{unsupported_tools_directory}
%dir %{_sysconfdir}/pki/nssdb
%config(noreplace) %{_sysconfdir}/pki/nssdb/cert8.db
%config(noreplace) %{_sysconfdir}/pki/nssdb/key3.db
%config(noreplace) %{_sysconfdir}/pki/nssdb/secmod.db
%dir %{_sysconfdir}/prelink.conf.d
%{_sysconfdir}/prelink.conf.d/nss-prelink.conf

%files tools
%defattr(-,root,root)
%{_bindir}/certutil
%{_bindir}/cmsutil
%{_bindir}/crlutil
%{_bindir}/modutil
%{_bindir}/pk12util
%{_bindir}/signtool
%{_bindir}/signver
%{_bindir}/ssltap
%{unsupported_tools_directory}/atob
%{unsupported_tools_directory}/btoa
%{unsupported_tools_directory}/derdump
%{unsupported_tools_directory}/ocspclnt
%{unsupported_tools_directory}/pp
%{unsupported_tools_directory}/selfserv
%{unsupported_tools_directory}/strsclnt
%{unsupported_tools_directory}/symkeyutil
%{unsupported_tools_directory}/tstclnt
%{unsupported_tools_directory}/vfyserv
%{unsupported_tools_directory}/vfychain


%files devel
%defattr(-,root,root)
%{_libdir}/libnss3.so
%{_libdir}/libnssutil3.so
%{_libdir}/libnssdbm3.so
%{_libdir}/libssl3.so
%{_libdir}/libsmime3.so
%{_libdir}/libsoftokn3.so
%{_libdir}/libsoftokn3.chk
%{_libdir}/libnssckbi.so
%{_libdir}/libnsspem.so
%{_libdir}/libfreebl3.so
%{_libdir}/libfreebl3.chk
%{_libdir}/libcrmf.a
%{_libdir}/pkgconfig/nss.pc
%{_bindir}/nss-config

%dir %{_includedir}/nss3
%{_includedir}/nss3/base64.h
%{_includedir}/nss3/blapit.h
%{_includedir}/nss3/cert.h
%{_includedir}/nss3/certdb.h
%{_includedir}/nss3/certt.h
%{_includedir}/nss3/ciferfam.h
%{_includedir}/nss3/cmmf.h
%{_includedir}/nss3/cmmft.h
%{_includedir}/nss3/cms.h
%{_includedir}/nss3/cmsreclist.h
%{_includedir}/nss3/cmst.h
%{_includedir}/nss3/crmf.h
%{_includedir}/nss3/crmft.h
%{_includedir}/nss3/cryptohi.h
%{_includedir}/nss3/cryptoht.h
%{_includedir}/nss3/ecl-exp.h
%{_includedir}/nss3/hasht.h
%{_includedir}/nss3/jar-ds.h
%{_includedir}/nss3/jar.h
%{_includedir}/nss3/jarfile.h
%{_includedir}/nss3/key.h
%{_includedir}/nss3/keyhi.h
%{_includedir}/nss3/keyt.h
%{_includedir}/nss3/keythi.h
%{_includedir}/nss3/nss.h
%{_includedir}/nss3/nssb64.h
%{_includedir}/nss3/nssb64t.h
%{_includedir}/nss3/nssckbi.h
%{_includedir}/nss3/nssilckt.h
%{_includedir}/nss3/nssilock.h
%{_includedir}/nss3/nsslocks.h
%{_includedir}/nss3/nsslowhash.h
%{_includedir}/nss3/nsspem.h
%{_includedir}/nss3/nssrwlk.h
%{_includedir}/nss3/nssrwlkt.h
%{_includedir}/nss3/ocsp.h
%{_includedir}/nss3/ocspt.h
%{_includedir}/nss3/p12.h
%{_includedir}/nss3/p12plcy.h
%{_includedir}/nss3/p12t.h
%{_includedir}/nss3/pk11func.h
%{_includedir}/nss3/pk11pqg.h
%{_includedir}/nss3/pk11priv.h
%{_includedir}/nss3/pk11pub.h
%{_includedir}/nss3/pk11sdr.h
%{_includedir}/nss3/pkcs11.h
%{_includedir}/nss3/pkcs11f.h
%{_includedir}/nss3/pkcs11n.h
%{_includedir}/nss3/pkcs11p.h
%{_includedir}/nss3/pkcs11t.h
%{_includedir}/nss3/pkcs11u.h
%{_includedir}/nss3/pkcs12.h
%{_includedir}/nss3/pkcs12t.h
%{_includedir}/nss3/pkcs7t.h
%{_includedir}/nss3/portreg.h
%{_includedir}/nss3/preenc.h
%{_includedir}/nss3/secasn1.h
%{_includedir}/nss3/secasn1t.h
%{_includedir}/nss3/seccomon.h
%{_includedir}/nss3/secder.h
%{_includedir}/nss3/secdert.h
%{_includedir}/nss3/secdig.h
%{_includedir}/nss3/secdigt.h
%{_includedir}/nss3/secerr.h
%{_includedir}/nss3/sechash.h
%{_includedir}/nss3/secitem.h
%{_includedir}/nss3/secmime.h
%{_includedir}/nss3/secmod.h
%{_includedir}/nss3/secmodt.h
%{_includedir}/nss3/secoid.h
%{_includedir}/nss3/secoidt.h
%{_includedir}/nss3/secpkcs5.h
%{_includedir}/nss3/secpkcs7.h
%{_includedir}/nss3/secport.h
%{_includedir}/nss3/shsign.h
%{_includedir}/nss3/smime.h
%{_includedir}/nss3/ssl.h
%{_includedir}/nss3/sslerr.h
%{_includedir}/nss3/sslproto.h
%{_includedir}/nss3/sslt.h
%{_includedir}/nss3/utilrename.h
%{_includedir}/nss3/watcomfx.h


%files pkcs11-devel
%defattr(-, root, root)
%{_includedir}/nss3/nssbase.h
%{_includedir}/nss3/nssbaset.h
%{_includedir}/nss3/nssckepv.h
%{_includedir}/nss3/nssckft.h
%{_includedir}/nss3/nssckfw.h
%{_includedir}/nss3/nssckfwc.h
%{_includedir}/nss3/nssckfwt.h
%{_includedir}/nss3/nssckg.h
%{_includedir}/nss3/nssckmdt.h
%{_includedir}/nss3/nssckt.h
%{_libdir}/libnssb.a
%{_libdir}/libnssckfw.a


%changelog
* Tue Mar 31 2009 Kai Engert <kaie@redhat.com> - 3.12.2.99.3-3
- add upstream patch to fix bug 483855
* Tue Mar 31 2009 Kai Engert <kaie@redhat.com> - 3.12.2.99.3-2
- build nspr-less freebl library
* Tue Mar 31 2009 Kai Engert <kaie@redhat.com> - 3.12.2.99.3-1
- Update to NSS_3_12_3_BETA4

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.12.2.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Oct 22 2008 Kai Engert <kaie@redhat.com> - 3.12.2.0-3
- update to NSS_3_12_2_RC1
- use system zlib
* Tue Sep 30 2008 Dennis Gilmore <dennis@ausil.us> - 3.12.1.1-4
- add sparc64 to the list of 64 bit arches

* Wed Sep 24 2008 Kai Engert <kaie@redhat.com> - 3.12.1.1-3
- bug 456847, move pkgconfig requirement to devel package
* Fri Sep 05 2008 Kai Engert <kengert@redhat.com> - 3.12.1.1-2
- Update to NSS_3_12_1_RC2
* Fri Aug 22 2008 Kai Engert <kaie@redhat.com> - 3.12.1.0-2
- NSS 3.12.1 RC1
* Fri Aug 15 2008 Kai Engert <kaie@redhat.com> - 3.12.0.3-7
- fix bug bug 429175 in libpem module
* Tue Aug 05 2008 Kai Engert <kengert@redhat.com> - 3.12.0.3-6
- bug 456847, add Requires: pkgconfig
* Tue Jun 24 2008 Kai Engert <kengert@redhat.com> - 3.12.0.3-3
- nss package should own /etc/prelink.conf.d folder, rhbz#452062
- use upstream patch to fix test suite abort
* Mon Jun 02 2008 Kai Engert <kengert@redhat.com> - 3.12.0.3-2
- Update to NSS_3_12_RC4
* Mon Apr 14 2008 Kai Engert <kengert@redhat.com> - 3.12.0.1-1
- Update to NSS_3_12_RC2
* Thu Mar 20 2008 Jesse Keating <jkeating@redhat.com> - 3.11.99.5-2
- Zapping old Obsoletes/Provides.  No longer needed, causes multilib headache.
* Mon Mar 17 2008 Kai Engert <kengert@redhat.com> - 3.11.99.5-1
- Update to NSS_3_12_BETA3
* Fri Feb 22 2008 Kai Engert <kengert@redhat.com> - 3.11.99.4-1
- NSS 3.12 Beta 2
- Use /usr/lib{64} as devel libdir, create symbolic links.
* Sat Feb 16 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-6
- Apply upstream patch for bug 417664, enable test suite on pcc.
* Fri Feb 15 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-5
- Support concurrent runs of the test suite on a single build host.
* Thu Feb 14 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-4
- disable test suite on ppc
* Thu Feb 14 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-3
- disable test suite on ppc64

* Thu Feb 14 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-2
- Build against gcc 4.3.0, use workaround for bug 432146
- Run the test suite after the build and abort on failures.

* Thu Jan 24 2008 Kai Engert <kengert@redhat.com> - 3.11.99.3-1
* NSS 3.12 Beta 1

* Mon Jan 07 2008 Kai Engert <kengert@redhat.com> - 3.11.99.2b-3
- move .so files to /lib

* Wed Dec 12 2007 Kai Engert <kengert@redhat.com> - 3.11.99.2b-2
- NSS 3.12 alpha 2b

* Mon Dec 03 2007 Kai Engert <kengert@redhat.com> - 3.11.99.2-2
- upstream patches to avoid calling netstat for random data

* Wed Nov 07 2007 Kai Engert <kengert@redhat.com> - 3.11.99.2-1
- NSS 3.12 alpha 2

* Wed Oct 10 2007 Kai Engert <kengert@redhat.com> - 3.11.7-10
- Add /etc/prelink.conf.d/nss-prelink.conf in order to blacklist
  our signed libraries and protect them from modification.

* Thu Sep 06 2007 Rob Crittenden <rcritten@redhat.com> - 3.11.7-9
- Fix off-by-one error in the PEM module

* Thu Sep 06 2007 Kai Engert <kengert@redhat.com> - 3.11.7-8
- fix a C++ mode compilation error

* Wed Sep 05 2007 Bob Relyea <rrelyea@redhat.com> - 3.11.7-7
- Add 3.12 ckfw and libnsspem

* Tue Aug 28 2007 Kai Engert <kengert@redhat.com> - 3.11.7-6
- Updated license tag

* Wed Jul 11 2007 Kai Engert <kengert@redhat.com> - 3.11.7-5
- Ensure the workaround for mozilla bug 51429 really get's built.

* Mon Jun 18 2007 Kai Engert <kengert@redhat.com> - 3.11.7-4
- Better approach to ship freebl/softokn based on 3.11.5
- Remove link time dependency on softokn

* Sun Jun 10 2007 Kai Engert <kengert@redhat.com> - 3.11.7-3
- Fix unowned directories, rhbz#233890

* Fri Jun 01 2007 Kai Engert <kengert@redhat.com> - 3.11.7-2
- Update to 3.11.7, but freebl/softokn remain at 3.11.5.
- Use a workaround to avoid mozilla bug 51429.

* Fri Mar 02 2007 Kai Engert <kengert@redhat.com> - 3.11.5-2
- Fix rhbz#230545, failure to enable FIPS mode
- Fix rhbz#220542, make NSS more tolerant of resets when in the 
  middle of prompting for a user password.

* Sat Feb 24 2007 Kai Engert <kengert@redhat.com> - 3.11.5-1
- Update to 3.11.5
- This update fixes two security vulnerabilities with SSL 2
- Do not use -rpath link option
- Added several unsupported tools to tools package

* Tue Jan  9 2007 Bob Relyea <rrelyea@redhat.com> - 3.11.4-4
- disable ECC, cleanout dead code

* Tue Nov 28 2006 Kai Engert <kengert@redhat.com> - 3.11.4-1
- Update to 3.11.4

* Thu Sep 14 2006 Kai Engert <kengert@redhat.com> - 3.11.3-2
- Revert the attempt to require latest NSPR, as it is not yet available
  in the build infrastructure.

* Thu Sep 14 2006 Kai Engert <kengert@redhat.com> - 3.11.3-1
- Update to 3.11.3

* Thu Aug 03 2006 Kai Engert <kengert@redhat.com> - 3.11.2-2
- Add /etc/pki/nssdb

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 3.11.2-1.1
- rebuild

* Fri Jun 30 2006 Kai Engert <kengert@redhat.com> - 3.11.2-1
- Update to 3.11.2
- Enable executable bit on shared libs, also fixes debug info.

* Wed Jun 14 2006 Kai Engert <kengert@redhat.com> - 3.11.1-2
- Enable Elliptic Curve Cryptography (ECC)

* Fri May 26 2006 Kai Engert <kengert@redhat.com> - 3.11.1-1
- Update to 3.11.1
- Include upstream patch to limit curves

* Wed Feb 15 2006 Kai Engert <kengert@redhat.com> - 3.11-4
- add --noexecstack when compiling assembler on x86_64

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 3.11-3.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 3.11-3.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Jan 19 2006 Ray Strode <rstrode@redhat.com> 3.11-3
- rebuild

* Fri Dec 16 2005 Christopher Aillon <caillon@redhat.com> 3.11-2
- Update file list for the devel packages

* Thu Dec 15 2005 Christopher Aillon <caillon@redhat.com> 3.11-1
- Update to 3.11

* Thu Dec 15 2005 Christopher Aillon <caillon@redhat.com> 3.11-0.cvs.2
- Add patch to allow building on ppc*
- Update the pkgconfig file to Require nspr

* Thu Dec 15 2005 Christopher Aillon <caillon@redhat.com> 3.11-0.cvs
- Initial import into Fedora Core, based on a CVS snapshot of
  the NSS_3_11_RTM tag
- Fix up the pkcs11-devel subpackage to contain the proper headers
- Build with RPM_OPT_FLAGS
- No need to have rpath of /usr/lib in the pc file

* Thu Dec 15 2005 Kai Engert <kengert@redhat.com>
- Adressed review comments by Wan-Teh Chang, Bob Relyea,
  Christopher Aillon.

* Tue Jul  9 2005 Rob Crittenden <rcritten@redhat.com> 3.10-1
- Initial build
