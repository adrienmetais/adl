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

import zipfile
import io
import argparse

def patch(raw_data, rights_content):
  buf = io.BytesIO(raw_data)
  z = zipfile.ZipFile(buf, mode='a')
  z.writestr("META-INF/rights.xml", rights_content)
  z.close()
  new_data = buf.getvalue()
  buf.close()
  return new_data

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Patch the epub file to add the rights.xml file')
  parser.add_argument('--filename', dest="filename", required=True,
                      help='The epub')

  args = parser.parse_args()

  with open(args.filename) as f:
    data = f.read()
    buf = patch(data, "<toto/>")
    
    with open("patched.epub", "w") as w:
      w.write(buf)
