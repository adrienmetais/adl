
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
import ConfigParser
import logging

import login
import epub_get

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Manipulate ACSM files')
  parser.add_argument('-c', '--config', dest="configfile", help="Configuration file path", default="adedl.conf")
  parser.add_argument('-v', '--verbose', dest="verbose", help="Log verbosely", action="store_true", default=False)
  parser.add_argument('-n', dest="dry", help="Do not perform actions", action="store_true", default=False)
  subparsers = parser.add_subparsers(title="commands", description="available commands", help="additional help")

  parser_get = subparsers.add_parser('get', help='Download ebook from an ACSM file')
  parser_get.add_argument('-f', '--filename', dest="filename", required=True, help='The ACSM file')
  parser_get.set_defaults(func=epub_get.get_ebook)

  parser_get = subparsers.add_parser('login', help='Login to Content Server')
  parser_get.set_defaults(func=login.login)

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
    loglevel = logging.WARN
  logging.basicConfig(format='%(levelname)s:%(message)s', level=loglevel)

  config = ConfigParser.RawConfigParser()
  config.read(args.configfile)

  # Call appropriate handler
  args.func(args, config)

