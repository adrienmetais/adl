import sqlite3
import base64

from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, add_subelement
import utils
import login
import device

db_file = 'adl.db'

class Config():
  def __init__(self, db_file):
    self.db_file = db_file
    self.auth_url = None
    self.userinfo_url = None
    self.activation_certificate = None
    self.authentication_certificate = None
    self.current_user = None

  def ready(self):
    return self.activation_certificate is not None and self.authentication_certificate is not None

  def load(self):
    conn = sqlite3.connect(self.db_file)
    conn.text_factory = str
    c = conn.cursor()

    rows = c.execute("select default_user, auth_url, activation_certificate, userinfo_url, authentication_certificate from configuration")
    config = rows.fetchone()
    self.current_user = config[0]
    self.auth_url = config[1]
    self.activation_certificate = config[2]
    self.userinfo_url = config[3]
    self.authentication_certificate = config[4]
    
    conn.close()

  def store(self):
    conn = sqlite3.connect(self.db_file)
    conn.text_factory = str
    c = conn.cursor()

    values = (self.current_user,
              self.auth_url,
              self.activation_certificate,
              self.userinfo_url,
              self.authentication_certificate)

    c.execute("insert into configuration (default_user, auth_url, activation_certificate, userinfo_url, authentication_certificate) values (?,?,?,?,?)", values)
   
    conn.commit() 
    conn.close()

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

  def store(self):
    conn = sqlite3.connect(db_file)
    conn.text_factory = str
    c = conn.cursor()
    ph = (self.urn, 
          self.sign_id, 
          self.sign_method, 
          self.auth_key[1],
          self.auth_key[0],
          self.license_key[1],
          self.license_key[0],
          self.pkcs12,
          self.encryptedPK,
          self.licenseCertificate)

    c.execute("insert into users values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ph)

    for d in self.devices:
      dph = (self.urn,
             d.device_key,
             d.device_id,
             d.fingerprint,
             d.name,
             d.type)
    c.execute("insert into devices values(?, ?, ?, ?, ?, ?)", dph)
    conn.commit()
    conn.close()

  def get_device(self, device_name):
    #devices = device.get_all_devices(self.urn)
    for d in self.devices:
      if d.name == device_name:
        return d
    return None

def get_all_accounts():
  accounts = []

  conn = sqlite3.connect(db_file)
  conn.text_factory = str
  c = conn.cursor()

  # TODO: explicitely list columns
  rows = c.execute("select * from users")
  for user in rows.fetchall():
    a = Account()
    a.urn, a.sign_id, a.sign_method, akpub, akpriv, lkpub, lkpriv, a.pkcs12, a.encryptedPK, a.licenseCertificate = user
    a.auth_key = (akpriv, akpub)
    a.license_key = (lkpriv, lkpub)
    a.devices = device.get_all_devices(a.urn)
    accounts.append(a)

  conn.close()

  return accounts

def get_account(user_id):
  accounts = get_all_accounts()
  for a in accounts:
    if a.urn == user_id:
      return a
  return None

def find_by_sign(sign):
  accounts = get_all_accounts()
  for a in accounts:
    if a.sign_id == sign:
      return a
  return None

def get_default_account():
  conn = sqlite3.connect(db_file)
  c = conn.cursor()
  row = c.execute("select default_user from configuration")
  da = row.fetchone()[0]
  conn.close() 
  
  return da

def set_default_account(args, config):
  urn = args.urn
  a = get_account(urn)
  if a is None:
    print('Unknown user')
    return
  conn = sqlite3.connect(db_file)
  c = conn.cursor()
  c.execute("update configuration set default_user=?", (urn,))
  conn.commit()
  conn.close() 

def cli_list(args, config):
  print("Accounts (* shows currently used account):")
  accounts = get_all_accounts()
  default = get_default_account()
  for a in accounts:
    marker = ' '
    if a.urn == default:
      marker = '*'
    print("- {} {} - {} ({})".format(marker, a.urn, a.sign_id, a.sign_method))

