%define nspr_version 4.6.2
%define unsupported_tools_directory %{_libdir}/nss/unsupported-tools
%define fips_source_version 3.11.5
%define ckbi_version 1.64

Summary:          Network Security Services
Name:             nss
Version:          3.11.7
Release:          5%{?dist}
License:          MPL/GPL/LGPL
URL:              http://www.mozilla.org/projects/security/pki/nss/
Group:            System Environment/Libraries
Requires:         nspr >= %{nspr_version}
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:    nspr-devel >= %{nspr_version}
BuildRequires:    pkgconfig
BuildRequires:    gawk
Provides:         mozilla-nss
Obsoletes:        mozilla-nss

#Source0:          %{name}-%{version}-no-fbst.tar.gz
Source0:          %{name}-%{version}-no-fbst-with-ckbi-%{ckbi_version}.tar.gz
# ckbi is the builtin roots module which may get released separately.

Source1:          nss.pc.in
Source2:          nss-config.in
Source3:          blank-cert8.db
Source4:          blank-key3.db
Source5:          blank-secmod.db
Source7:          fake-kstat.h
Source10:         %{name}-%{fips_source_version}-fbst-stripped.tar.gz

Patch1:           nss-no-rpath.patch
Patch2:           nss-smartcard-auth.patch
Patch3:           nss-use-netstat-hack.patch
Patch4:           nss-decouple-softokn.patch
Patch5:           nss-disable-build-freebl-softoken.patch


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
Provides:         mozilla-nss-devel
Obsoletes:        mozilla-nss-devel

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
%setup -q -T -D -n %{name}-%{version} -a 10

%define old_nss_lib %{name}-%{fips_source_version}/mozilla/security/nss/lib
%define new_nss_lib mozilla/security/nss/lib

# Ensure we will not use new freebl/softoken code
rm -rf %{new_nss_lib}/freebl
rm -rf %{new_nss_lib}/softoken

# However, in order to build newer NSS we need some exports
cp -a %{old_nss_lib}/freebl %{new_nss_lib}
cp -a %{old_nss_lib}/softoken %{new_nss_lib}

# Ensure the newer NSS tree will not build code, except the loader
mv -i %{new_nss_lib}/freebl/loader.c %{new_nss_lib}/freebl/loader.c.save
rm -rf %{new_nss_lib}/freebl/*.c %{new_nss_lib}/freebl/*.s
rm -rf %{new_nss_lib}/softoken/*.c %{new_nss_lib}/softoken/*.s
mv -i %{new_nss_lib}/freebl/loader.c.save %{new_nss_lib}/freebl/loader.c

# These currently don't build without freebl/softoken in the same tree
rm -rf mozilla/security/nss/cmd/bltest
rm -rf mozilla/security/nss/cmd/fipstest
rm -rf mozilla/security/nss/cmd/certcgi

# Apply the patches to the newer NSS tree
%patch1 -p0
%patch2 -p0 -b .smartcard-auth
%patch4 -p0 -b .decouple-softokn
%patch5 -p0 -b .nofbst

# Apply the patches to the tree where we build freebl/softoken
cd nss-%{fips_source_version}
%patch3 -p0 -b .use-netstat-hack
%{__mkdir_p} mozilla/security/nss/lib/fake/
cp -i %{SOURCE7} mozilla/security/nss/lib/fake/kstat.h
cd ..


%build

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

%ifarch x86_64 ppc64 ia64 s390x
USE_64=1
export USE_64
%endif

# NSS_ENABLE_ECC=1
# export NSS_ENABLE_ECC

##### first, build freebl and softokn shared libraries

cd nss-%{fips_source_version}
%{__make} -C ./mozilla/security/coreconf
%{__make} -C ./mozilla/security/dbm
%{__make} -C ./mozilla/security/nss export
%{__make} -C ./mozilla/security/nss/lib/base
%{__make} -C ./mozilla/security/nss/lib/util
%{__make} -C ./mozilla/security/nss/lib/freebl
touch ./mozilla/security/nss/lib/freebl/unix_rand.c
rm -f ./mozilla/security/nss/lib/freebl/*/*/libfreebl3*
rm -f ./mozilla/security/nss/lib/freebl/*/*/sysrand*
USE_NETSTAT_HACK=1 %{__make} -C ./mozilla/security/nss/lib/freebl
%{__make} -C ./mozilla/security/nss/lib/freebl install
%{__make} -C ./mozilla/security/nss/lib/softoken
%{__make} -C ./mozilla/security/nss/lib/softoken install
cd ..

##### second, build all the rest of NSS

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


%install

# There is no make install target so we'll do it ourselves.

%{__mkdir_p} $RPM_BUILD_ROOT/%{_includedir}/nss3
%{__mkdir_p} $RPM_BUILD_ROOT/%{_bindir}
%{__mkdir_p} $RPM_BUILD_ROOT/%{_libdir}
%{__mkdir_p} $RPM_BUILD_ROOT/%{unsupported_tools_directory}

# Copy the binary libraries we want
for file in libsoftokn3.so libfreebl3.so
do
  %{__install} -m 755 nss-%{fips_source_version}/mozilla/dist/*.OBJ/lib/$file \
                      $RPM_BUILD_ROOT/%{_libdir}
done

# Copy the binary libraries we want
for file in libnss3.so libssl3.so libsmime3.so libnssckbi.so
do
  %{__install} -m 755 mozilla/dist/*.OBJ/lib/$file $RPM_BUILD_ROOT/%{_libdir}
done

# These ghost files will be generated in the post step
touch $RPM_BUILD_ROOT/%{_libdir}/libsoftokn3.chk
touch $RPM_BUILD_ROOT/%{_libdir}/libfreebl3.chk

# Install the empty NSS db files
%{__mkdir_p} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb
%{__install} -m 644 %{SOURCE3} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/cert8.db
%{__install} -m 644 %{SOURCE4} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/key3.db
%{__install} -m 644 %{SOURCE5} $RPM_BUILD_ROOT/%{_sysconfdir}/pki/nssdb/secmod.db

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

# Copy the include files we want from freebl/softoken sources
# and remove those files from the other area
for file in blapit.h shsign.h ecl-exp.h pkcs11.h pkcs11f.h pkcs11p.h pkcs11t.h pkcs11n.h pkcs11u.h
do
  %{__install} -m 644 nss-%{fips_source_version}/mozilla/dist/public/nss/$file \
                      $RPM_BUILD_ROOT/%{_includedir}/nss3
  rm mozilla/dist/public/nss/$file
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
%{unsupported_tools_directory}/shlibsign -i %{_libdir}/libsoftokn3.so >/dev/null 2>/dev/null
%{unsupported_tools_directory}/shlibsign -i %{_libdir}/libfreebl3.so >/dev/null 2>/dev/null


%postun
/sbin/ldconfig >/dev/null 2>/dev/null


%files
%defattr(-,root,root)
%{_libdir}/libnss3.so
%{_libdir}/libssl3.so
%{_libdir}/libsmime3.so
%{_libdir}/libsoftokn3.so
%{_libdir}/libnssckbi.so
%{_libdir}/libfreebl3.so
%{unsupported_tools_directory}/shlibsign
%ghost %{_libdir}/libsoftokn3.chk
%ghost %{_libdir}/libfreebl3.chk
%dir %{_libdir}/nss
%dir %{unsupported_tools_directory}
%dir %{_sysconfdir}/pki/nssdb
%config(noreplace) %{_sysconfdir}/pki/nssdb/cert8.db
%config(noreplace) %{_sysconfdir}/pki/nssdb/key3.db
%config(noreplace) %{_sysconfdir}/pki/nssdb/secmod.db

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
