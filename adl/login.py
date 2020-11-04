import requests
import logging
import os
import base64

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography import x509

from lxml import etree

from xml_tools import ADEPT_NS, NSMAP
from account import Account

def parse_activationinfo_reply(reply):
  tree_root = etree.fromstring(reply)
  auth_url = tree_root.find("{http://ns.adobe.com/adept}authURL").text
  userinfo_url = tree_root.find("{http://ns.adobe.com/adept}userInfoURL").text
  activation_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
  return auth_url, userinfo_url, activation_certificate

def parse_authinfo_reply(reply):
  tree_root = etree.fromstring(reply)
  auth_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
  return auth_certificate

def parse_signin_reply(reply):
  tree_root = etree.fromstring(reply)
  user = tree_root.find("{http://ns.adobe.com/adept}user").text
  pkcs12 = tree_root.find("{http://ns.adobe.com/adept}pkcs12").text
  epk = tree_root.find("{http://ns.adobe.com/adept}encryptedPrivateLicenseKey").text
  lcert = tree_root.find("{http://ns.adobe.com/adept}licenseCertificate").text
  return (user, pkcs12, epk, lcert)

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

def build_sign_in_request(auth_data, akp, lkp):
  # TODO: base64 all inputs - Maybe not needed ?
  xml = etree.Element("{%s}signIn" % ADEPT_NS, nsmap=NSMAP, attrib = {"method": "anonymous"})
  sign_data = etree.Element("signInData")
  sign_data.text = base64.b64encode(auth_data)
  xml.append(sign_data)

  pub_ak = etree.Element("publicAuthKey")
  pub_ak.text = akp[1]
  xml.append(pub_ak)

  epak = etree.Element("encryptedPrivateAuthKey")
  epak.text = akp[0]
  xml.append(epak)

  pub_lk = etree.Element("publicLicenseKey")
  pub_lk.text = lkp[1]
  xml.append(pub_lk)

  eplk = etree.Element("encryptedPrivateLicenseKey")
  eplk.text = lkp[0]
  xml.append(eplk)

  return etree.tostring(xml)

def generate_device_key():
  # Not exactly sure how it is really generated in ADE
  # However as it changes each time, I am guessing it is ok to generate it randomly
  return os.urandom(16)

def aes_crypt(msg, key):
  iv = os.urandom(16)
  cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
  encryptor = cipher.encryptor()

  padder = padding.PKCS7(128).padder()
  padded_data = padder.update(msg) + padder.finalize()

  ct = iv + encryptor.update(padded_data) + encryptor.finalize()
  return base64.b64encode(ct)

def generate_key_pair():
  key = rsa.generate_private_key(
      backend=crypto_default_backend(),
      public_exponent=65537,
      key_size=1024
  )

  private_key = key.private_bytes(
      crypto_serialization.Encoding.DER,
      crypto_serialization.PrivateFormat.PKCS8,
      crypto_serialization.NoEncryption())

  public_key = key.public_key().public_bytes(
      crypto_serialization.Encoding.DER,
      crypto_serialization.PublicFormat.SubjectPublicKeyInfo
  )

  return (base64.b64encode(private_key), base64.b64encode(public_key))

def sign_in(account):
  account.device_key = generate_device_key()

  # Only supported method for the moment
  account.sign_method = "anonymous"

  # device key
  # 0 if no username, else:
  #  Size of username
  #  username (UTF-8)
  # 0 if no password, else:
  #  Size of password
  #  password (UTF-8)

  auth_data = [ord(i) for i in account.device_key]
  auth_data.append(0) # null username
  auth_data.append(0) # null password

  # Get certificate
  certificate = x509.load_der_x509_certificate(base64.b64decode(account.authentication_certificate))

  # generate auth key pair
  account.auth_key = generate_key_pair()

  # generate license key pair
  account.license_key = generate_key_pair()

  # Encrypt with public auth service certificate
  serialized_auth_data = "".join([chr(i) for i in auth_data])
  public_auth_key = certificate.public_key()
  encrypted_auth_data = public_auth_key.encrypt(serialized_auth_data, asym_padding.PKCS1v15())

  # Encrypt key pairs with device key
  encrypted_akp = (aes_crypt(base64.b64decode(account.auth_key[0]), account.device_key), account.auth_key[1])
  encrypted_lkp = (aes_crypt(base64.b64decode(account.license_key[0]), account.device_key), account.license_key[1])

  xml_str = build_sign_in_request(encrypted_auth_data, encrypted_akp, encrypted_lkp)
  
  #print(xml_str)

  svc = "SignInDirect"
  url = "http://adeactivate.adobe.com/adept/"+svc
  try:
    headers = {'content-type': 'application/vnd.adobe.adept+xml'}
    r = requests.post(url, data = xml_str, headers = headers)
    r.raise_for_status()
    #print r.text
    account.urn, account.pkcs12, account.encryptedPK, account.licenseCertificate = parse_signin_reply(r.text)
  except Exception:
    logging.exception("Could not contact activation server")

def login(args, config):
  acc = Account()

  activation_init()
  acc.authentication_certificate = authentication_init()
  sign_in(acc)

  # Store
  acc.store()
