import logging
import base64

from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography import x509

from .bom import Account, Device
from . import utils
from . import device
from .api_call import ActivationInit, AuthenticationInit, SignInDirect
from . import data

def login(user, password):
  acc = Account()

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
  actinit = ActivationInit()
  return actinit.call()

########## Auth Info ###########

def authentication_init():
  authinit = AuthenticationInit()
  return authinit.call()

######### Sign In ###########

def generate_auth_data(user, password, binary_device_key):
  # device key
  # 0 if no username, else:
  #  Size of username
  #  username (UTF-8)
  # 0 if no password, else:
  #  Size of password
  #  password (UTF-8)

  auth_data = bytearray(binary_device_key)
  if user is None:
    auth_data.append(0) # null username
  else:
    auth_data.append(len(user))
    auth_data.extend(user.encode('utf-8'))

  if password is None:
    auth_data.append(0) # null password
  else:
    auth_data.append(len(password))
    auth_data.extend(password.encode('utf-8'))

  serialized_auth_data = bytes(auth_data)

  return serialized_auth_data

def sign_in(data, acc, user, password):
  d = Device()
  d.generate_key()
  d.generate_fingerprint()

  # Only supported methods for the moment
  if user is None or password is None:
    acc.sign_method = "anonymous"
    logging.warning("WARNING: logging in as anonymous - please see README for risks")
  else:
    acc.sign_method = "AdobeID"
    acc.sign_id = user

  binary_device_key = base64.b64decode(d.device_key)
  serialized_auth_data = generate_auth_data(user, password, binary_device_key)

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

  signin = SignInDirect(acc.sign_method, encrypted_auth_data, encrypted_akp, encrypted_lkp)
  success, acc.urn, acc.pkcs12, acc.encryptedPK, acc.licenseCertificate = signin.call() 

  return success

