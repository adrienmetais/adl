#!/usr/bin/env python

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

import login
import epub_get
import account
import device

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Manipulate ACSM files')
  parser.add_argument('-c', '--config', dest="config_db", help="Configuration db file path", default="adl.db")
  parser.add_argument('-v', '--verbose', dest="verbose", help="Log verbosely", action="store_true", default=False)
  parser.add_argument('-n', dest="dry", help="Do not perform actions", action="store_true", default=False)
  subparsers = parser.add_subparsers(title="commands", description="available commands", help="additional help")

  parser_get = subparsers.add_parser('get', help='Download ebook from an ACSM file')
  parser_get.add_argument('-f', '--filename', dest="filename", required=True, help='The ACSM file')
  parser_get.set_defaults(func=epub_get.get_ebook)

  parser_login = subparsers.add_parser('login', help='Login to Content Server')
  parser_login.add_argument('-u', '--user', dest="user", default=None, help='Login with this Adobe ID')
  parser_login.set_defaults(func=login.login)

  parser_account = subparsers.add_parser('account', help='Manage accounts')
  account_sp = parser_account.add_subparsers()
  parser_alist = account_sp.add_parser('list', help='list accounts')
  parser_alist.set_defaults(func=account.cli_list)
  parser_aset = account_sp.add_parser('use', help='Set account to use')
  parser_aset.add_argument('urn', help='The user urn')
  parser_aset.set_defaults(func=account.set_default_account)

  parser_device = subparsers.add_parser('device', help='Manage devices')
  device_sp = parser_device.add_subparsers()
  parser_dlist = device_sp.add_parser('list', help='list devices')
  parser_dlist.set_defaults(func=device.device_list)
  parser_detect = device_sp.add_parser('register', help='Register reader')
  parser_detect.add_argument('mountpoint', help='Reader root fs mountpoint')
  parser_detect.set_defaults(func=device.device_register)

  # Future options could include:
  # * Register to Adobe
  # * Send file to device
  # * Configuration
  # * Retrieve keys from existing ADE install

  # TODO: no relative paths ?
  # TODO: store params in db

  args = parser.parse_args()

  if args.verbose:
    loglevel = logging.DEBUG
  else:
    loglevel = logging.INFO
  logging.basicConfig(format='%(levelname)s:%(message)s', level=loglevel)

  config = account.Config(args.config_db)
  config.load()

  # Call appropriate handler
  args.func(args, config)

