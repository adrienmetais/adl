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

from lxml import etree
import struct
import re
import hashlib
import base64

from .crypto import RSAHandler

from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives import hashes

BEGIN_ELEMENT=1
END_ATTRIBUTES=2
END_ELEMENT=3
TEXT_NODE=4
ATTRIBUTE=5

ADEPT_NS="http://ns.adobe.com/adept"
NSMAP = {None: ADEPT_NS}

def add_byte(o, i):
  o = o + struct.pack('B', i);
  return o

def add_str(o, s):
  o = o + struct.pack('>H', len(s))
  o = o + s.encode('ascii')
  return o

def parse_namespace(tag, default_ns):
  m = re.match("{(.*)}(.*)", tag)
  if m is not None:
    return m.group(2), m.group(1)
  else:
    return tag, default_ns

def serialize(node):
  out = bytes()
  name, ns = parse_namespace(node.tag, ADEPT_NS)
  if name in ["hmac", "signature"]:
    return ""
  out = add_byte(out, BEGIN_ELEMENT)
  out = add_str(out, ns)
  out = add_str(out, name)
  for attr_name in sorted(node.attrib.keys()):
    out = add_byte(out, ATTRIBUTE)
    out = add_str(out, "")
    out = add_str(out, attr_name)
    out = add_str(out, str(node.attrib[attr_name]))
  out = add_byte(out, END_ATTRIBUTES)
  for child in node:
    out = out + serialize(child)
  # In ActionScript, the text field is a child
  # Here it should work because the XML has either children or text
  if node.text is not None and node.text.strip() != "":
    out = add_byte(out, TEXT_NODE)
    out = add_str(out, node.text.strip())
  out = add_byte(out, END_ELEMENT)
  return out

def xml_hash(s):
  h = hashlib.sha1()
  h.update(s)
  d = h.hexdigest()
  # Force big endian
  return b"".join(struct.pack('>I', int(d[i*8:i*8+8], 16)) for i in range(5))

# key as byte array
def encrypt(hxml, key):
  rsa = RSAHandler(key)
  sig = rsa.encrypt(hxml)

  return sig

def generate_signature(xml_str, key):
  xml = etree.fromstring(xml_str)
  # First normalize and serialize the XML
  sxml = serialize(xml)
  # Compute the sha1
  hxml = xml_hash(sxml)
  # Encrypt it with private key
  sig = encrypt(hxml, key)
  return base64.b64encode(sig)

def sign_xml(element, pk):
  xml_str = etree.tostring(element)

  signature = etree.Element("signature")
  signature.text = generate_signature(xml_str, pk)
  element.append(signature)

  return element
  
def add_subelement(element, name, text):
  e = etree.Element(name)
  e.text = text
  element.append(e)
  return e

def get_error(xml):
  tree_root = etree.fromstring(xml)
  if 'error' in tree_root.tag:
    return tree_root.get('data')
  return None

