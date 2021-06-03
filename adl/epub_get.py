import logging
import requests
import base64
from lxml import etree

from .xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement, get_error
from . import utils
from . import patch_epub
from . import account
from . import data
from .api_call import FFAuth, InitLicense, Fulfillment

def parse_acsm(acsm_filename):
  fftoken = etree.parse(acsm_filename)
  token_root = fftoken.getroot()

  operator = token_root.find("{http://ns.adobe.com/adept}operatorURL").text

  return operator, token_root

def log_in(config, acc, operator):
  ffauth = FFAuth(operator, acc, config)
  result = ffauth.call()

  if result:
    init_license = InitLicense(operator, acc)
    result = init_license.call()
    return result
  else:
    logging.info(get_error(result))
    return False

def generate_rights_xml(license_token):
  adobe_certificate = "MIIEvjCCA6agAwIBAgIER2q5ljANBgkqhkiG9w0BAQUFADCBhDELMAkGA1UEBhMCVVMxIzAhBgNVBAoTGkFkb2JlIFN5c3RlbXMgSW5jb3Jwb3JhdGVkMRswGQYDVQQLExJEaWdpdGFsIFB1Ymxpc2hpbmcxMzAxBgNVBAMTKkFkb2JlIENvbnRlbnQgU2VydmVyIENlcnRpZmljYXRlIEF1dGhvcml0eTAeFw0wODA4MTExNjMzNDhaFw0xMzA4MTEwNzAwMDBaMIGIMQswCQYDVQQGEwJVUzEjMCEGA1UEChMaQWRvYmUgU3lzdGVtcyBJbmNvcnBvcmF0ZWQxGzAZBgNVBAsTEkRpZ2l0YWwgUHVibGlzaGluZzE3MDUGA1UEAxMuaHR0cHM6Ly9uYXNpZ25pbmdzZXJ2aWNlLmFkb2JlLmNvbS9saWNlbnNlc2lnbjCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAs9GRZ1f5UTRySgZ2xAL7TaDKQBfdpIS9ei9Orica0N72BB/WE+82G5lfsZ2HdeCFDZG/oz2WPLXovcuUAbFKSIXVLyc7ONOd4sczeXQYPixeAvqzGtsyMArIzaeJcriGVPRnbD/spbuHR0BHhJEakIiDtQLJz+xgVYHlicx2H/kCAwEAAaOCAbQwggGwMAsGA1UdDwQEAwIFoDBYBglghkgBhvprHgEESwxJVGhlIHByaXZhdGUga2V5IGNvcnJlc3BvbmRpbmcgdG8gdGhpcyBjZXJ0aWZpY2F0ZSBtYXkgaGF2ZSBiZWVuIGV4cG9ydGVkLjAUBgNVHSUEDTALBgkqhkiG9y8CAQIwgbIGA1UdIASBqjCBpzCBpAYJKoZIhvcvAQIDMIGWMIGTBggrBgEFBQcCAjCBhhqBg1lvdSBhcmUgbm90IHBlcm1pdHRlZCB0byB1c2UgdGhpcyBMaWNlbnNlIENlcnRpZmljYXRlIGV4Y2VwdCBhcyBwZXJtaXR0ZWQgYnkgdGhlIGxpY2Vuc2UgYWdyZWVtZW50IGFjY29tcGFueWluZyB0aGUgQWRvYmUgc29mdHdhcmUuMDEGA1UdHwQqMCgwJqAkoCKGIGh0dHA6Ly9jcmwuYWRvYmUuY29tL2Fkb2JlQ1MuY3JsMB8GA1UdIwQYMBaAFIvu8IFgyaLaHg5SwVgMBLBD94/oMB0GA1UdDgQWBBSQ5K+bvggI6Rbh2u9nPhH8bcYTITAJBgNVHRMEAjAAMA0GCSqGSIb3DQEBBQUAA4IBAQC0l1L+BRCccZdb2d9zQBJ7JHkXWt1x/dUydU9I/na+QPFE5x+fGK4cRwaIfp6fNviGyvtJ6Wnxe6du/wlarC1o26UNpyWpnAltcy47LpVXsmcV5rUlhBx10l4lecuX0nx8/xF8joRz2BvvAusK+kxgKeiAjJg2W20wbJKh0Otct1ZihruQsEtGbZJ1L55xfNhrm6CKAHuGuTDYQ/S6W20dUaDUiNFhA2n2eEySLwUwgOuuhfVUPb8amQQKbF4rOQ2rdjAskEl/0CiavW6Xv0LGihThf6CjEbNSdy+vXQ7K9wFbKsE843DflpuSPfj2Aagtyrv/j1HsBjsf03e0uVu5"

  #etree.ElementTree.register_namespace("adept", ADEPT_NS) 
  rights = etree.Element("{%s}rights" % ADEPT_NS, nsmap=NSMAP)
  rights.append(license_token)
  lsi = etree.Element("{%s}licenseServiceInfo" % ADEPT_NS, nsmap=NSMAP)
  add_subelement(lsi, "licenseURL", "https://nasigningservice.adobe.com/licensesign")
  add_subelement(lsi, "certificate", adobe_certificate)
  rights.append(lsi)
  
  return etree.tostring(rights, doctype='<?xml version="1.0"?>')

def fulfill(acsm_content, a, operator):
  logging.info("Sending fullfilment request")
  ff = Fulfillment(acsm_content, a, operator)
  return ff.call()

def get_ebook(filename):
  logging.info("Opening {} ...".format(filename))

  a = data.get_current_account()
  if a is None:
    logging.error("Please log in with a user and select it first")
    return

  try:
    # The ACSM file contains a "fulfillment URL" that we must query
    # in order to get the real file URL
    operator, acsm_content = parse_acsm(filename)

    if not log_in(data.config, a, operator):
      logging.info("Failed to init license")
      return

    title, ebook_url, license_token = fulfill(acsm_content, a, operator)

    # Get epub URL and download it
    logging.info("Downloading {} from {} ...".format(title, ebook_url))
    r = requests.get(ebook_url)
    r.raise_for_status()
    epub = r.content

    # A file containing the license token must be added to the epub
    logging.info("Patching epub ...")
    rights_xml = generate_rights_xml(license_token)    
    patched_epub = patch_epub.patch(epub, rights_xml)

    # Write file to disc
    # TODO: configurable output ?
    epub_filename = "{0}.epub".format(title)
    logging.info("Writing {} ...".format(epub_filename))
    with open(epub_filename, "wb") as epub_file:
      epub_file.write(patched_epub)

    logging.info("Successfully downloaded file {}".format(epub_filename))
  except:
    logging.exception("Error when downloading book !")

