import sqlite3
import base64

db_file = 'adl.db'

class Device():
  def __init__(self):
    self.device_key = None
    self.device_id = None
    self.fingerprint = None
    self.type = 'standalone'

  def __str__(self):
    return "{}: {}".format(self.device_id, self.device_key)

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

  def store(self):
    conn = sqlite3.connect(db_file)
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
             base64.b64encode(d.device_key),
             d.device_id,
             d.fingerprint)
    c.execute("insert into devices values(?, ?, ?, ?)", dph)
    conn.commit()
    conn.close()

def get_all_accounts():
  accounts = []

  conn = sqlite3.connect(db_file)
  c = conn.cursor()

  # TODO: explicitely list columns
  users = c.execute("select * from users")
  for user in users:
    a = Account()
    a.urn, a.sign_id, a.sign_method, akpub, akpriv, lkpub, lkpriv, a.pkcs12, a.encryptedPK, a.licenseCertificate = user
    a.auth_key = (akpriv, akpub)
    a.license_key = (lkpriv, lkpub)
    devices = c.execute("select device_key, device_id from devices where user_id=?", (a.urn,))
    for device in devices:
      d = Device()
      d.device_key, d.device_id = device
      a.devices.append(d)
    accounts.append(a)

  conn.close()

  return accounts

def get_account(user_id):
  accounts = get_all_accounts()
  for a in accounts:
    if a.urn == user_id:
      return a
  return None

def get_default_account():
  conn = sqlite3.connect(db_file)
  c = conn.cursor()
  row = c.execute("select default_user from configuration")
  da = row.fetchone()[0]
  conn.close() 
  
  return da

def cli_list(args, config):
  print("Accounts:")
  accounts = get_all_accounts()
  for a in accounts:
    print("* {} - {} ({})".format(a.urn, a.sign_id, a.sign_method))


