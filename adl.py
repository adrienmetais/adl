#!/usr/bin/env python3

# Copyright (C) 2020
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import logging
import sys
import getpass

from adl import login, epub_get, account, device, db, data

def adobe_login(args):
  password = None
  if args.user is not None:
    password = getpass.getpass()

  login.login(args.user, password)

def list_accounts(args):
  print("Accounts (* shows currently used account):")
  for a in data.accounts:
    marker = ' '
    if a.urn == data.config.current_user:
      marker = '*'
    print(("- {} {} - {} ({})".format(marker, a.urn, a.sign_id, a.sign_method)))

def delete_account(args):
  account.account_delete(args.urn)

def set_default_account(args):
  account.set_default_account(args.urn)

def get_ebook(args):
  epub_get.get_ebook(args.filename)

def list_devices(args):
  print("Known devices:")
  a = data.get_current_account()
  if a is not None:
    for d in a.devices:
      print(("-  {} {} - {} ".format(d.name, d.device_id, d.type)))
  else:
    print("No registered device")

def register_device(args):
  device.device_register(args.mountpoint)

parser = argparse.ArgumentParser(description='Manipulate ACSM files')
parser.add_argument('-v', '--verbose', dest="verbose", help="Log verbosely", action="store_true", default=False)
subparsers = parser.add_subparsers(title="commands", description="available commands", help="additional help")

parser_get = subparsers.add_parser('get', help='Download ebook from an ACSM file')
parser_get.add_argument('-f', '--filename', dest="filename", required=True, help='The ACSM file')
parser_get.set_defaults(func=get_ebook)

parser_login = subparsers.add_parser('login', help='Login to Content Server')
parser_login.add_argument('-u', '--user', dest="user", default=None, help='Login with this Adobe ID')
parser_login.set_defaults(func=adobe_login)

parser_account = subparsers.add_parser('account', help='Manage accounts')
account_sp = parser_account.add_subparsers()
parser_alist = account_sp.add_parser('list', help='list accounts')
parser_alist.set_defaults(func=list_accounts)
parser_adel = account_sp.add_parser('delete', help='delete account (be careful !)')
parser_adel.add_argument('urn', help='The user urn')
parser_adel.set_defaults(func=delete_account)
parser_aset = account_sp.add_parser('use', help='Set account to use')
parser_aset.add_argument('urn', help='The user urn')
parser_aset.set_defaults(func=set_default_account)

parser_device = subparsers.add_parser('device', help='Manage devices for current user')
device_sp = parser_device.add_subparsers()
parser_dlist = device_sp.add_parser('list', help='list devices')
parser_dlist.set_defaults(func=list_devices)
parser_detect = device_sp.add_parser('register', help='Register reader')
parser_detect.add_argument('mountpoint', help='Reader root fs mountpoint')
parser_detect.set_defaults(func=register_device)

args = parser.parse_args()

if not hasattr(args, 'func'):
  parser.print_help()
  sys.exit(1)

# TODO now that adl is a package:
#   - Method should not "print" anything but return lists
#   - Data should not go through here
#   - module names do not really make sense

if args.verbose:
  loglevel = logging.DEBUG
else:
  loglevel = logging.INFO
logging.basicConfig(format='%(levelname)s:%(message)s', level=loglevel)

# Call appropriate handler
args.func(args)

