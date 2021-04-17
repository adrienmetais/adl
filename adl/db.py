import sqlite3
import os
import logging

from .bom import Account, Config, Device

class DBData:
  def __init__(self):
    self.config = None
    self.accounts = []
    self.db = DB()
    self.db_path = "{}/.adl".format(os.environ["HOME"])
    self.db_file = 'adl.db'

  def check_or_create_dir(self):
    if os.path.exists(self.db_path):
      if os.path.isdir(self.db_path):
          return True
      else:
        logging.error("{} is not a directory, please remove it and try again")
        return False
    else:
      logging.info("~/.adl/ does not exist: creating it")
      os.mkdir(self.db_path)

    return True

  def load(self):
    self.db.connect()
    try:
      self.config = self.db.load_config()
      self.accounts = self.db.load_accounts()
    except Exception:
      logging.exception("Exception occurred during db load !")
    self.db.disconnect()

  def set_current_account(self, account_urn):
    self.db.connect()

    try:
      if find_account_by_urn(account_urn) is None:
        logging.error("Unknown user")
      else:
        self.config.current_user = account_urn
        self.db.update_current_user(account_urn)
    except Exception:
      logging.exception("Exception occurred when setting current user !")

    self.db.disconnect()
  
  def add_account(self, a):
    self.db.connect()
    
    try:
      if find_account_by_urn(a.urn) is not None:
        logging.error("Account already exists - this should not happen")
      else:
        self.accounts.append(a)
        self.db.add_account(a)
    except Exception:
      logging.exception("Exception occurred when adding an account !")

    self.db.disconnect()

  def delete_account(self, a):
    self.db.connect()
    
    try:
      self.accounts.remove(a)
      self.db.delete_account(a)
    except Exception:
      logging.exception("Exception occurred when deleting account !")

    self.db.disconnect()
    
  def add_device(self, a, d):
    self.db.connect()
    
    try:
      a = find_account_by_urn(a.urn)
      if a is None:
        logging.error("Account does not exist - this should not happen")
      else:
        if d.device_id not in [dev.device_id for dev in a.devices]:
          a.devices.append(d)
        self.db.add_device(a.urn, d)
    except Exception:
      logging.error("Exception occurred when adding a device !")

    self.db.disconnect()

  def store_config(self, conf):
    self.db.connect()

    try:
      if self.config is not None:
        # Not possible to update for the moment
        logging.error("Config already exists - this should not happend")
      else:
        self.db.store_config(conf)
    except Exception:
      logging.error("Exception occurred during db load !")

    self.db.disconnect()

  def find_account_by_urn(self, urn):
    for a in self.accounts:
      if a.urn == urn:
        return a
    return None

  def find_account_by_sign(self, sign):
    for a in self.accounts:
      if a.sign_id == sign:
        return a
    return None

  def get_current_account(self):
    a = None
    if self.config is not None and self.config.current_user is not None:
      a = self.find_account_by_urn(self.config.current_user)
    return a


class DB:
  DB_TABLES = {
                "users": {
                  "user_id": "text PRIMARY KEY",
                  "sign_id": "text",
                  "sign_method": "text",
                  "auth_pub": "text",
                  "auth_priv": "text",
                  "license_pub": "text",
                  "license_priv": "text",
                  "pkcs12": "text",
                  "eplk": "text",
                  "license_certificate": "text"
                },
                "devices": {
                  "user_id": "text",
                  "device_key": "text",
                  "device_id": "text PRIMARY KEY",
                  "fingerprint": "text",
                  "device_name": "text",
                  "device_type": "text"
                },
                "configuration": {
                  "default_user": "text",
                  "auth_url": "text",
                  "activation_certificate": "text",
                  "userinfo_url": "text",
                  "authentication_certificate": "text"
                }
              }
  
  def __init__(self):
    self.db_path = "{}/.adl".format(os.environ["HOME"])
    self.db_file = 'adl.db'

  def connect(self):
    self.connector = sqlite3.connect("{}/{}".format(self.db_path, self.db_file))
    self.connector.text_factory = str
    self.create_tables()

  def disconnect(self):
    self.connector.commit()
    self.connector.close()
    self.connector = None

  # For migration purposes
  def check_column_exists(self, table_name, col_name):
    c = self.connector.cursor()
    c.execute("PRAGMA table_info('{}')".format(table_name))
    rows = c.fetchall()
    for row in rows:
      if col_name == row[1]:
        return True
    return False

  def check_table_exists(self, table_name):
    c = self.connector.cursor()
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}'".format(table_name))
    return c.fetchone()[0] == 1

  def create_tables(self):
    c = self.connector.cursor()
    for table_name, columns in list(self.DB_TABLES.items()):
      if self.check_table_exists(table_name):
        continue

      col_cmd = []
      for col_name, col_type in list(columns.items()):
        if col_name != "pk":
          col_cmd.append("{} {}".format(col_name, col_type))
        else:
          col_cmd.append(col_type)

      cmd = "create table {} ({})".format(table_name, ",".join(col_cmd))
      c.execute(cmd)

    # Do migrations here

    self.connector.commit()

  def load_config(self):
    c = self.connector.cursor()

    # Config
    rows = c.execute("select default_user, auth_url, activation_certificate, userinfo_url, authentication_certificate from configuration")
    config = rows.fetchone()
    conf = None

    if config is not None:
      conf = Config()
      conf.current_user = config[0]
      conf.auth_url = config[1]
      conf.activation_certificate = config[2]
      conf.userinfo_url = config[3]
      conf.authentication_certificate = config[4]

    return conf

  def load_accounts(self):
    c = self.connector.cursor()

    # Users
    accounts = []
    rows = c.execute("select user_id, sign_id, sign_method, auth_pub, auth_priv, license_pub, license_priv, pkcs12, eplk, license_certificate from users")
    for user in rows.fetchall():
      a = Account()
      accounts.append(a)

      a.urn, a.sign_id, a.sign_method, akpub, akpriv, lkpub, lkpriv, a.pkcs12, a.encryptedPK, a.licenseCertificate = user
      a.auth_key = (akpriv, akpub)
      a.license_key = (lkpriv, lkpub)
      a.devices = []

      # Devices
      rows = c.execute("select device_name, device_key, device_id, fingerprint, device_type from devices where user_id=?", (a.urn,))
      for dev in rows.fetchall():
        d = Device()
        d.name, d.device_key, d.device_id, d.fingerprint, d.type = dev
        a.devices.append(d)

    return accounts

  def store_config(self, conf):
    c = self.connector.cursor()

    values = (conf.current_user,
              conf.auth_url,
              conf.activation_certificate,
              conf.userinfo_url,
              conf.authentication_certificate)

    c.execute("insert into configuration (default_user, auth_url, activation_certificate, userinfo_url, authentication_certificate) values (?,?,?,?,?)", values)

    self.connector.commit()

  def add_account(self, a):
    c = self.connector.cursor()

    ph = (a.urn, 
          a.sign_id, 
          a.sign_method, 
          a.auth_key[1],
          a.auth_key[0],
          a.license_key[1],
          a.license_key[0],
          a.pkcs12,
          a.encryptedPK,
          a.licenseCertificate)

    c.execute("insert into users values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ph)

    self.connector.commit()

  def delete_account(self, a):
    c = self.connector.cursor()

    c.execute("delete from devices where user_id=?", (a.urn,))
    c.execute("delete from users where user_id=?", (a.urn,))

    self.connector.commit()

  def add_device(self, account_urn, d):
    c = self.connector.cursor()

    dph = (account.urn,
           d.device_key,
           d.device_id,
           d.fingerprint,
           d.name,
           d.type)

    c.execute("insert into devices values(?, ?, ?, ?, ?, ?)", dph)

    self.connector.commit()

  def update_current_user(self, account_urn):
    c = self.connector.cursor()

    c.execute("update configuration set default_user=?", (account_urn,))

    self.connector.commit()
 
