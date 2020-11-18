import requests
import logging
import os
import base64
import datetime
import struct
import hashlib

from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography import x509

from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement
from account import Account, Device
import utils

def login(args, config):
  acc = Account()

  activation_init()
  acc.authentication_certificate = authentication_init()
  sign_in(acc)

  activate(acc)

  # Store
  acc.store()

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

######### Activation ###########

def get_expiration_date():
  return datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(minutes=30), "%Y-%m-%dT%H:%M:%S-00:00")

def build_activation_request(acc):
  device = acc.devices[0] # TODO: better
  xml = etree.Element("{%s}activate" % ADEPT_NS, nsmap=NSMAP, attrib = {"requestType": "initial"})
  add_subelement(xml, "fingerprint", device.fingerprint)
  add_subelement(xml, "deviceType", device.type)
  add_subelement(xml, "clientOS", "Windows Vista")
  add_subelement(xml, "clientLocale", "en") # TODO: is it useful to set the real locale ?
  add_subelement(xml, "clientVersion", "ADE WIN 9,0,1131,27")
  add_subelement(xml, "nonce", utils.make_nonce())
  add_subelement(xml, "expiration", get_expiration_date()) 
  add_subelement(xml, "user", acc.urn)

  pk = utils.extract_pk_from_pcks12(acc, device.device_key)
  xml = sign_xml(xml, pk)

  return etree.tostring(xml)

def activate(acc):
  # Activate this computer
  xml_str = build_activation_request(acc)

  svc = "Activate"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    headers = {'content-type': 'application/vnd.adobe.adept+xml'}
    r = requests.post(url, data = xml_str, headers = headers)
    r.raise_for_status()
    device_id = parse_activation_reply(r.text)
  except Exception:
    logging.exception("Could not contact activation server")

  acc.devices[0].device_id = device_id

def parse_activation_reply(reply):
  tree_root = etree.fromstring(reply)
  device_id = tree_root.find("{http://ns.adobe.com/adept}device").text
  return device_id


######### Sign In ###########

def build_sign_in_request(auth_data, akp, lkp):
  xml = etree.Element("{%s}signIn" % ADEPT_NS, nsmap=NSMAP, attrib = {"method": "anonymous"})
  add_subelement(xml, "signInData", base64.b64encode(auth_data))
  add_subelement(xml, "publicAuthKey", akp[1])
  add_subelement(xml, "encryptedPrivateAuthKey", akp[0])
  add_subelement(xml, "publicLicenseKey", lkp[1])
  add_subelement(xml, "encryptedPrivateLicenseKey", lkp[0])

  return etree.tostring(xml)

def generate_device_key():
  # Not exactly sure how it is really generated in ADE
  # However as it changes each time, I am guessing it is ok to generate it randomly
  device_key = os.urandom(16)
  return device_key

def generate_device_fingerprint():
  # Not sure this is portable
  # Also not the same way it is generated by ADE. Is it an issue ?
  with open('/etc/machine-id', 'r') as f:
    h = hashlib.sha1()
    h.update(f.read())
    d = h.digest()
    return base64.b64encode(d)

def sign_in(acc):
  device = Device()
  device.device_key = generate_device_key()
  device.fingerprint = generate_device_fingerprint()
  acc.devices.append(device)

  # Only supported method for the moment
  acc.sign_method = "anonymous"

  # device key
  # 0 if no username, else:
  #  Size of username
  #  username (UTF-8)
  # 0 if no password, else:
  #  Size of password
  #  password (UTF-8)

  auth_data = [ord(i) for i in device.device_key]
  auth_data.append(0) # null username
  auth_data.append(0) # null password
  serialized_auth_data = "".join([chr(i) for i in auth_data])

  # Get certificate
  certificate = x509.load_der_x509_certificate(base64.b64decode(acc.authentication_certificate))

  # generate auth key pair
  acc.auth_key = utils.generate_key_pair()

  # generate license key pair
  acc.license_key = utils.generate_key_pair()

  # Encrypt with public auth service certificate
  public_auth_key = certificate.public_key()
  encrypted_auth_data = public_auth_key.encrypt(serialized_auth_data, asym_padding.PKCS1v15())

  # Encrypt key pairs with device key
  encrypted_akp = (utils.aes_crypt(base64.b64decode(acc.auth_key[0]), device.device_key), acc.auth_key[1])
  encrypted_lkp = (utils.aes_crypt(base64.b64decode(acc.license_key[0]), device.device_key), acc.license_key[1])

  xml_str = build_sign_in_request(encrypted_auth_data, encrypted_akp, encrypted_lkp)
  
  svc = "SignInDirect"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    headers = {'content-type': 'application/vnd.adobe.adept+xml'}
    r = requests.post(url, data = xml_str, headers = headers)
    r.raise_for_status()
    acc.urn, acc.pkcs12, acc.encryptedPK, acc.licenseCertificate = parse_signin_reply(r.text)
  except Exception:
    logging.exception("Could not contact activation server")

def parse_signin_reply(reply):
  tree_root = etree.fromstring(reply)
  user = tree_root.find("{http://ns.adobe.com/adept}user").text
  pkcs12 = tree_root.find("{http://ns.adobe.com/adept}pkcs12").text
  epk = tree_root.find("{http://ns.adobe.com/adept}encryptedPrivateLicenseKey").text
  lcert = tree_root.find("{http://ns.adobe.com/adept}licenseCertificate").text
  return (user, pkcs12, epk, lcert)

