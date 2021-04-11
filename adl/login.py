import requests
import logging
import os
import base64
import datetime
import struct
import hashlib
import getpass

from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography import x509

from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement, get_error
from account import Account
import utils
import device

# TODO: enforce dry mode
def login(args, data):
  acc = Account()
  password = None
  if args.user is not None:
    password = getpass.getpass()

  if data.config is None:
    data.config = Config()

  if not data.config.ready():
    data.config.auth_url, data.config.userinfo_url, data.config.activation_certificate = activation_init()
    data.config.authentication_certificate = authentication_init()
    data.store_config()

  if not sign_in(data, acc, args.user, password):
    logging.error('Sign in error')
    return

  # Activate this computer
  d = acc.get_device('local')
  device.activate(acc, d)

  # Store
  data.add_account(acc)
  data.add_device(acc.urn, d)
  data.set_current_account(acc.urn)

########### Activation Info ############

def activation_init():
  svc = "ActivationServiceInfo"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    r = requests.get(url)
    r.raise_for_status()
    return parse_activationinfo_reply(r.text)
  except Exception:
    logging.exception("Could not contact activation server")
    return None, None, None

def parse_activationinfo_reply(reply):
  tree_root = etree.fromstring(reply)
  auth_url = tree_root.find("{http://ns.adobe.com/adept}authURL").text
  userinfo_url = tree_root.find("{http://ns.adobe.com/adept}userInfoURL").text
  activation_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
  return auth_url, userinfo_url, activation_certificate

########## Auth Info ###########

def authentication_init():
  svc = "AuthenticationServiceInfo"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    r = requests.get(url)
    r.raise_for_status()
    return parse_authinfo_reply(r.text)
  except Exception:
    logging.exception("Could not contact authentication server")
    return None

def parse_authinfo_reply(reply):
  tree_root = etree.fromstring(reply)
  auth_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
  return auth_certificate

######### Sign In ###########

def build_sign_in_request(auth_data, akp, lkp, method):
  xml = etree.Element("{%s}signIn" % ADEPT_NS, nsmap=NSMAP, attrib = {"method": method})
  add_subelement(xml, "signInData", base64.b64encode(auth_data))
  add_subelement(xml, "publicAuthKey", akp[1])
  add_subelement(xml, "encryptedPrivateAuthKey", akp[0])
  add_subelement(xml, "publicLicenseKey", lkp[1])
  add_subelement(xml, "encryptedPrivateLicenseKey", lkp[0])

  return etree.tostring(xml)

def sign_in(data, acc, user, password):
  d = device.Device()
  d.device_key = device.generate_device_key()
  d.fingerprint = device.generate_device_fingerprint()

  # Only supported methods for the moment
  if user is None or password is None:
    acc.sign_method = "anonymous"
    logging.warning("WARNING: logging in as anonymous - please see README for risks")
  else:
    acc.sign_method = "AdobeID"
    acc.sign_id = user

  # device key
  # 0 if no username, else:
  #  Size of username
  #  username (UTF-8)
  # 0 if no password, else:
  #  Size of password
  #  password (UTF-8)

  binary_device_key = base64.b64decode(d.device_key)
  auth_data = [ord(i) for i in binary_device_key]
  if user is None:
    auth_data.append(0) # null username
  else:
    # TODO: should be utf8
    auth_data.append(len(user))
    auth_data.extend([ord(i) for i in user])

  if password is None:
    auth_data.append(0) # null password
  else:
    # TODO: should be utf8
    auth_data.append(len(password))
    auth_data.extend([ord(i) for i in password])

  serialized_auth_data = "".join([chr(i) for i in auth_data])

  # Get certificate
  certificate = x509.load_der_x509_certificate(base64.b64decode(data.config.authentication_certificate))

  # generate auth key pair
  acc.auth_key = utils.generate_key_pair()

  # generate license key pair
  acc.license_key = utils.generate_key_pair()

  # Encrypt with public auth service certificate
  public_auth_key = certificate.public_key()
  encrypted_auth_data = public_auth_key.encrypt(serialized_auth_data, asym_padding.PKCS1v15())

  # Encrypt key pairs with device key
  encrypted_akp = (utils.aes_crypt(base64.b64decode(acc.auth_key[0]), binary_device_key), acc.auth_key[1])
  encrypted_lkp = (utils.aes_crypt(base64.b64decode(acc.license_key[0]), binary_device_key), acc.license_key[1])

  xml_str = build_sign_in_request(encrypted_auth_data, encrypted_akp, encrypted_lkp, acc.sign_method)
  
  svc = "SignInDirect"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    headers = {'content-type': 'application/vnd.adobe.adept+xml'}
    r = requests.post(url, data = xml_str, headers = headers)
    r.raise_for_status()
    if 'error' in r.text:
      error = get_error(r.text)
      logging.error(error)
      return False

    acc.urn, acc.pkcs12, acc.encryptedPK, acc.licenseCertificate = parse_signin_reply(r.text)
  except Exception:
    logging.exception("Could not contact activation server")

  return True

def parse_signin_reply(reply):
  tree_root = etree.fromstring(reply)
  user = tree_root.find("{http://ns.adobe.com/adept}user").text
  pkcs12 = tree_root.find("{http://ns.adobe.com/adept}pkcs12").text
  epk = tree_root.find("{http://ns.adobe.com/adept}encryptedPrivateLicenseKey").text
  lcert = tree_root.find("{http://ns.adobe.com/adept}licenseCertificate").text
  return (user, pkcs12, epk, lcert)

