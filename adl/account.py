import sqlite3
import base64

db_file = 'adl.db'

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

  def __str__(self):
    sign = "Sign {} ({}) - {}".format(self.sign_id, self.sign_method, self.urn)
    device = "Device {}".format(self.device_key)
    auth = "Auth key pair: {}".format(self.auth_key)
    license = "License key pair: {}".format(self.license_key)
    pkcs12 = "PKCS12: {}".format(self.pkcs12)
    epk = "Encrypted PK: {}".format(self.encryptedPK)
    lc = "License Certificate: {}".format(self.licenseCertificate)
    auth_cert = "Authentication certificate: {}".format(self.authentication_certificate)
    return '\n'.join([sign, device, auth, license, pkcs12, epk, lc, auth_cert])

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

    dph = (self.urn,
           base64.b64encode(self.device_key),
           None)
    c.execute("insert into devices values(?, ?, ?)", dph)
    conn.commit()
    conn.close()
