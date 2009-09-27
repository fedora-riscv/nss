#!/bin/sh
#
# Turns on or off the nss-sysinit module db by editing the
# global PKCS #11 congiguration file.
#
# This script can be invoked by the user as super user.
# It is invoked at nss-sysinit post install time with argument on
# and at nss-sysinit pre uninstall with argument off. 
#
usage()
{
  cat <<EOF
Usage: setup-nsssysinit [on|off]
  on  - turns on nsssysinit
  off - turns off nsssysinit
EOF
  exit $1
}

# validate
if test $# -eq 0; then
  usage 1 1>&2
fi

on="1"
case "$1" in
  on  | ON )  on="1";;
  off | OFF ) on="";;
  * )         usage 1 1>&2;;
esac

# the system-wide configuration file
p11conf="/etc/pki/nssdb/pkcs11.txt"
# must exist, otherwise report it and exit with failure
if [ ! -f $p11conf ]; then
  echo "Could not find ${p11conf}"
  exit 1
fi

# turn on or off
if [ on = "1" ]; then 
  cat ${p11conf} | sed -e 's/^library=$/library=libnsssysinit.so/' \
                       -e 'g/^NSS/ s; Flags=internal,critical; Flags=internal,moduleDBOnly,critical;' > \
                       ${p11conf}.on
  mv ${p11conf}.on ${p11conf}
else
  if [ `grep "^library=libnsssysinit" ${p11conf}` == ""]; then
    exit 0
  fi
  cat ${p11conf} | sed -e 's/^library=libnsssysinit.so/library=/' \
                       -e 'g/^NSS/ s; Flags=internal,moduleDBOnly,critical; Flags=internal,critical;' > \
                       ${p11conf}.off
  mv ${p11conf}.off ${p11conf}
fi

