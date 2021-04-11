import base64
import logging
import os

from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, add_subelement
import utils
import login
import device

class Config():
  def __init__(self):
    self.db_file = None
    self.auth_url = None
    self.userinfo_url = None
    self.activation_certificate = None
    self.authentication_certificate = None
    self.current_user = None

  def ready(self):
    return self.activation_certificate is not None and self.authentication_certificate is not None

class Account():
  def __init__(self):
    self.sign_method = None
    self.sign_id = None
    self.device_key = None
    self.auth_key = (None, None)
    self.license_key = (None, None)
    self.urn = None
    self.pkcs12 = None
    self.encryptedPK = None
    self.licenseCertificate = None
    self.authentication_certificate = None
    self.devices = []

  def __str__(self):
    sign = "Sign {} ({}) - {}".format(self.sign_id, self.sign_method, self.urn)
    auth = "Auth key pair: {}".format(self.auth_key)
    license = "License key pair: {}".format(self.license_key)
    pkcs12 = "PKCS12: {}".format(self.pkcs12)
    epk = "Encrypted PK: {}".format(self.encryptedPK)
    lc = "License Certificate: {}".format(self.licenseCertificate)
    auth_cert = "Authentication certificate: {}".format(self.authentication_certificate)
    return '\n'.join([sign, auth, license, pkcs12, epk, lc, auth_cert])

  def get_private_key(self):
    d = self.get_device('local')
    pk = utils.aes_decrypt(base64.b64decode(self.encryptedPK), base64.b64decode(d.device_key))
    return pk

  def get_device(self, device_name):
    for d in self.devices:
      if d.name == device_name:
        return d
    return None

def set_default_account(args, data):
  data.set_current_account(args.urn)

def cli_list(args, data):
  print("Accounts (* shows currently used account):")
  for a in data.accounts:
    marker = ' '
    if a.urn == data.config.current_user:
      marker = '*'
    print("- {} {} - {} ({})".format(marker, a.urn, a.sign_id, a.sign_method))

def account_delete(args, data):
  a = data.find_account_by_urn(args.urn)
  if a is None:
    print("Account does not exist")
  else:
    data.delete_account(a)
    print("Account deleted")
