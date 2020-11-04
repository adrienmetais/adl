#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ctypes import CDLL, POINTER, c_char_p, c_int, c_long, \
  Structure, create_string_buffer, cast
from ctypes.util import find_library

libcrypto = find_library('crypto')

if libcrypto is None:
  raise Exception('libcrypto not found')
libcrypto = CDLL(libcrypto)

RSA_PKCS1_PADDING = 1

c_char_pp = POINTER(c_char_p)
c_int_p = POINTER(c_int)

class RSA(Structure):
  pass
RSA_p = POINTER(RSA)

def F(restype, name, argtypes):
  func = getattr(libcrypto, name)
  func.restype = restype
  func.argtypes = argtypes
  return func

d2i_RSAPrivateKey = F(RSA_p, 'd2i_RSAPrivateKey',
                    [RSA_p, c_char_pp, c_long])
RSA_size = F(c_int, 'RSA_size', [RSA_p])
RSA_private_encrypt = F(c_int, 'RSA_private_encrypt',
                      [c_int, c_char_p, c_char_p, RSA_p, c_int])
RSA_free = F(None, 'RSA_free', [RSA_p])

ERR_get_error = F(c_long, 'ERR_get_error', [])
ERR_error_string = F(c_char_p, 'ERR_error_string', [c_long, c_char_p])

class RSAHandler(object):
  def __init__(self, der):
      buf = create_string_buffer(der)
      pp = c_char_pp(cast(buf, c_char_p))
      rsa = self._rsa = d2i_RSAPrivateKey(None, pp, len(der))
      if rsa is None:
          raise ADEPTError('Error parsing ADEPT user key DER')

  def encrypt(self, from_):
      rsa = self._rsa
      to = create_string_buffer(RSA_size(rsa))
      tolen = c_int();
      result = RSA_private_encrypt(len(from_), from_, to, rsa, RSA_PKCS1_PADDING)
      if result == -1:
        err = create_string_buffer(256)
        err = ERR_error_string(ERR_get_error(), err)
        print(err)
        raise Exception('RSA encryption failed')
      return to

  def __del__(self):
      if self._rsa is not None:
          RSA_free(self._rsa)
          self._rsa = None

