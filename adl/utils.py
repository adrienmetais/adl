import struct
import base64
import os
import time
import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization

nbnonce = 0

def make_nonce():
  global nbnonce
  # int(start_timestamp as epoch in miliseconds), int(nb nonce)
  its = int(time.time()*1000) & 0xFFFFFFFF
  d = struct.pack('!II', its, nbnonce)
  nbnonce += 1
  return base64.b64encode(d)

def get_expiration_date():
  return datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(minutes=30), "%Y-%m-%dT%H:%M:%S-00:00")

def extract_pk_from_pkcs12(acc, device_key):
  pk, _, _ = pkcs12.load_key_and_certificates(base64.b64decode(acc.pkcs12), device_key)

  pk_der = pk.private_bytes(
      crypto_serialization.Encoding.DER,
      crypto_serialization.PrivateFormat.TraditionalOpenSSL,
      crypto_serialization.NoEncryption())

  return pk_der

def extract_cert_from_pkcs12(acc, device_key):
  _ , cert, _ = pkcs12.load_key_and_certificates(base64.b64decode(acc.pkcs12), device_key)

  cert_der = cert.public_bytes(crypto_serialization.Encoding.DER)

  return cert_der

def aes_crypt(msg, key):
  iv = os.urandom(16)
  cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
  encryptor = cipher.encryptor()

  padder = padding.PKCS7(128).padder()
  padded_data = padder.update(msg) + padder.finalize()

  ct = iv + encryptor.update(padded_data) + encryptor.finalize()
  return base64.b64encode(ct)

def aes_decrypt(msg, key):
  iv = os.urandom(16)
  cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
  decryptor = cipher.decryptor()

  data = decryptor.update(msg) + decryptor.finalize()
  unpadder = padding.PKCS7(128).unpadder()
  pt = unpadder.update(data) + unpadder.finalize()

  return base64.b64encode(pt[16:])
  
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

