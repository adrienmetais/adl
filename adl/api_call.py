import logging
import requests
import base64
from lxml import etree

from .xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement, get_error
from . import utils

class APICall:
  def __init__(self):
    self.method = "post"

  def call(self):
    content = self.build()
    url = self.get_url()

    reply = self.send(url, content)

    return self.parse(reply)

  def send(self, url, data_str):
    headers = {'Content-type': 'application/vnd.adobe.adept+xml'}
    logging.debug(data_str)

    try:
      if self.method == "post":
        r = requests.post(url, data=data_str, headers=headers)
      elif self.method == "get":
        r = requests.get(url)
      r.raise_for_status()
      reply = r.text
    except Exception:
      logging.exception("Error when targeting {}".format(url))
      return None

    logging.debug(reply)
    return reply

###################################
class FFAuth(APICall):
  def __init__(self, operator, acc, config):
    APICall.__init__(self)
    self.acc = acc
    self.config = config
    self.operator = operator

  def get_url(self):
    return "{}/Auth".format(self.operator)

  def build(self):
    ff = etree.Element("{%s}credentials" % ADEPT_NS, nsmap=NSMAP)
    add_subelement(ff, "user", self.acc.urn)

    dev = self.acc.get_device('local')
    certificate = utils.extract_cert_from_pkcs12(self.acc, dev.device_key)

    add_subelement(ff, "certificate", base64.b64encode(certificate))
    add_subelement(ff, "licenseCertificate", self.acc.licenseCertificate)
    add_subelement(ff, "authenticationCertificate", self.config.authentication_certificate)
    return etree.tostring(ff)

  def parse(self, reply):
    return (reply is not None and "success" in reply)
    
###################################
class InitLicense(APICall):
  def __init__(self, operator, acc):
    APICall.__init__(self)
    self.acc = acc
    self.operator = operator

  def get_url(self):
    return "http://adeactivate.adobe.com/adept/InitLicenseService"

  def build(self):
    ff = etree.Element("{%s}licenseServiceRequest" % ADEPT_NS, nsmap=NSMAP, attrib = {"identity": "user"})
    add_subelement(ff, "operatorURL", self.operator)
    add_subelement(ff, "nonce", utils.make_nonce())
    add_subelement(ff, "expiration", utils.get_expiration_date())
    add_subelement(ff, "user", self.acc.urn)

    dev = self.acc.get_device('local')
    pk = utils.extract_pk_from_pkcs12(self.acc, dev.device_key)
    ff = sign_xml(ff, pk)

    return etree.tostring(ff)

  def parse(self, reply):
    return (reply is not None and "success" in reply)

###################################
class Fulfillment(APICall):
  def __init__(self, acsm_content, acc, operator):
    APICall.__init__(self)
    self.acc = acc
    self.acsm_content = acsm_content
    self.operator = operator

  def get_url(self):
    return "{0}/Fulfill".format(self.operator)

  def build(self):
    dev = self.acc.get_device('local')

    ff = etree.Element("{%s}fulfill" % ADEPT_NS, nsmap=NSMAP)
    add_subelement(ff, "user", self.acc.urn)

    if dev.device_id is not None:
      add_subelement(ff, "device", dev.device_id)
      add_subelement(ff, "deviceType", dev.type)

    ff.append(self.acsm_content)

    pk = utils.extract_pk_from_pkcs12(self.acc, dev.device_key)
    ff = sign_xml(ff, pk)

    return etree.tostring(ff)

  def parse(self, ff_reply):
    if ff_reply is None:
      return (None, None, None)

    tree_root = etree.fromstring(ff_reply)
    ff = tree_root.find("{http://ns.adobe.com/adept}fulfillmentResult")
    rii = ff.find("{http://ns.adobe.com/adept}resourceItemInfo")
    license = rii.find("{http://ns.adobe.com/adept}licenseToken")
    ebook_url = rii.find("{http://ns.adobe.com/adept}src").text
    metadata = rii.find("{http://ns.adobe.com/adept}metadata")
    title = metadata.find("{http://purl.org/dc/elements/1.1/}title").text

    return (title, ebook_url, license)

###################################
class Activate(APICall):
  def __init__(self, acc, dev):
    APICall.__init__(self)
    self.acc = acc
    self.device = dev

  def get_url(self):
    return "http://adeactivate.adobe.com/adept/Activate"

  def build(self):
    xml = etree.Element("{%s}activate" % ADEPT_NS, nsmap=NSMAP, attrib = {"requestType": "initial"})
    add_subelement(xml, "fingerprint", self.device.fingerprint)
    add_subelement(xml, "deviceType", self.device.type)
    add_subelement(xml, "clientOS", "Windows Vista")
    add_subelement(xml, "clientLocale", "en") # TODO: is it useful to set the real locale ?
    add_subelement(xml, "clientVersion", "ADE WIN 9,0,1131,27")
    add_subelement(xml, "nonce", utils.make_nonce())
    add_subelement(xml, "expiration", utils.get_expiration_date()) 
    add_subelement(xml, "user", self.acc.urn)

    local_device = self.acc.get_device('local')
    pk = utils.extract_pk_from_pkcs12(self.acc, local_device.device_key)
    xml = sign_xml(xml, pk)

    return etree.tostring(xml)

  def parse(self, reply):
    if reply is None:
      return None

    tree_root = etree.fromstring(reply)
    self.device.device_id = tree_root.find("{http://ns.adobe.com/adept}device").text
    return reply  

###################################
class ActivationInit(APICall):
  def __init__(self):
    APICall.__init__(self)
    self.method = "get"

  def get_url(self):
    return "http://adeactivate.adobe.com/adept/ActivationServiceInfo"

  def build(self):
    # GET request
    pass

  def parse(self, reply):
    if reply is None:
      return (None, None, None)

    tree_root = etree.fromstring(reply)
    auth_url = tree_root.find("{http://ns.adobe.com/adept}authURL").text
    userinfo_url = tree_root.find("{http://ns.adobe.com/adept}userInfoURL").text
    activation_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
    return auth_url, userinfo_url, activation_certificate

###################################
class AuthenticationInit(APICall):
  def __init__(self):
    APICall.__init__(self)
    self.method = "get"

  def get_url(self):
    return "http://adeactivate.adobe.com/adept/AuthenticationServiceInfo"

  def build(self):
    # GET request
    pass

  def parse(self, reply):
    if reply is None:
      return None

    tree_root = etree.fromstring(reply)
    auth_certificate = tree_root.find("{http://ns.adobe.com/adept}certificate").text
    return auth_certificate

###################################
class SignInDirect(APICall):
  def __init__(self, method, auth_data, akp, lkp):
    APICall.__init__(self)
    self.sign_method = method
    self.auth_data = auth_data
    self.akp = akp
    self.lkp = lkp

  def get_url(self):
    return "http://adeactivate.adobe.com/adept/SignInDirect"

  def build(self):
    xml = etree.Element("{%s}signIn" % ADEPT_NS, nsmap=NSMAP, attrib = {"method": self.sign_method})
    add_subelement(xml, "signInData", base64.b64encode(self.auth_data))
    add_subelement(xml, "publicAuthKey", self.akp[1])
    add_subelement(xml, "encryptedPrivateAuthKey", self.akp[0])
    add_subelement(xml, "publicLicenseKey", self.lkp[1])
    add_subelement(xml, "encryptedPrivateLicenseKey", self.lkp[0])

    return etree.tostring(xml)

  def parse(self, reply):
    if reply is None:
      return False, None, None, None, None

    if b'error' in reply:
      error = get_error(reply)
      logging.error(error)
      return False, None, None, None, None

    tree_root = etree.fromstring(reply)
    user = tree_root.find("{http://ns.adobe.com/adept}user").text
    pkcs12 = tree_root.find("{http://ns.adobe.com/adept}pkcs12").text
    epk = tree_root.find("{http://ns.adobe.com/adept}encryptedPrivateLicenseKey").text
    lcert = tree_root.find("{http://ns.adobe.com/adept}licenseCertificate").text
    return (True, user, pkcs12, epk, lcert)
