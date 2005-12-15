# Makefile for source rpm: nss
# $Id$
NAME := nss
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
