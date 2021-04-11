import logging
import requests
from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement, get_error
import utils
import patch_epub
import account
import base64

def parse_acsm(acsm_filename):
  fftoken = etree.parse(acsm_filename)
  token_root = fftoken.getroot()

  operator = token_root.find("{http://ns.adobe.com/adept}operatorURL").text

  return operator, token_root

def build_fulfillment_auth(acc, config):
  ff = etree.Element("{%s}credentials" % ADEPT_NS, nsmap=NSMAP)
  add_subelement(ff, "user", acc.urn)

  # TODO: choose appropriate device ?
  dev = acc.devices[0]
  certificate = utils.extract_cert_from_pkcs12(acc, dev.device_key)
  add_subelement(ff, "certificate", base64.b64encode(certificate))
  add_subelement(ff, "licenseCertificate", acc.licenseCertificate)
  add_subelement(ff, "authenticationCertificate", config.authentication_certificate)
  return etree.tostring(ff)

def build_license_request(operator, acc):
  ff = etree.Element("{%s}licenseServiceRequest" % ADEPT_NS, nsmap=NSMAP, attrib = {"identity": "user"})
  add_subelement(ff, "operatorURL", operator)
  add_subelement(ff, "nonce", utils.make_nonce())
  add_subelement(ff, "expiration", utils.get_expiration_date())
  add_subelement(ff, "user", acc.urn)

  dev = acc.devices[0]
  pk = utils.extract_pk_from_pkcs12(acc, dev.device_key)
  ff = sign_xml(ff, pk)

  return etree.tostring(ff)

def send(url, data_str, dry_mode):
  headers = {'content-type': 'application/vnd.adobe.adept+xml'}
  logging.info(data_str)

  if dry_mode:
    logging.info("(Dry run - Not sent)")
    return 

  try:
    r = requests.post(url, data=data_str, headers=headers)
    r.raise_for_status()
    reply = r.text
  except Exception:
    logging.error("Error when targeting {}".format(url))
    return None

  logging.info(reply)
  return reply

def log_in(config, acc, operator, dry_mode):
  xmlstr = build_fulfillment_auth(acc, config)
  url = "{}/Auth".format(operator)
  reply = send(url, xmlstr, dry_mode)
  if dry_mode or (reply is not None and "success" in reply):
    xmlstr = build_license_request(operator, acc)
    url = "http://adeactivate.adobe.com/adept/InitLicenseService"
    reply = send(url, xmlstr, dry_mode)
    return dry_mode or (reply is not None and "success" in reply)
  else:
    logging.info(get_error(reply))
    return False

def build_fulfillment_request(acsm_content, acc):
  # TODO: choose appropriate device ?
  dev = acc.get_device('local')

  ff = etree.Element("{%s}fulfill" % ADEPT_NS, nsmap=NSMAP)
  add_subelement(ff, "user", acc.urn)

  if dev.device_id is not None:
    add_subelement(ff, "device", dev.device_id)
    add_subelement(ff, "deviceType", dev.type)

  ff.append(acsm_content)

  pk = utils.extract_pk_from_pkcs12(acc, dev.device_key)
  ff = sign_xml(ff, pk)

  return etree.tostring(ff)

def parse_fulfillment_reply(ff_reply):
  tree_root = etree.fromstring(ff_reply)
  ff = tree_root.find("{http://ns.adobe.com/adept}fulfillmentResult")
  rii = ff.find("{http://ns.adobe.com/adept}resourceItemInfo")
  license = rii.find("{http://ns.adobe.com/adept}licenseToken")
  ebook_url = rii.find("{http://ns.adobe.com/adept}src").text
  metadata = rii.find("{http://ns.adobe.com/adept}metadata")
  title = metadata.find("{http://purl.org/dc/elements/1.1/}title").text
  return (title, ebook_url, etree.tostring(license))

def get_ebook(args, config):
  logging.info("Opening {} ...".format(args.filename))

  user = account.get_default_account()
  a = account.get_account(user)

  # The ACSM file contains a "fulfillment URL" that we must query
  # in order to get the real file URL
  operator, acsm_content = parse_acsm(args.filename)

  if not log_in(config, a, operator, args.dry):
    logging.info("Failed to init license")
    return

  ff_request = build_fulfillment_request(acsm_content, a)

  url = "{0}/Fulfill".format(operator)
  headers = {"Content-type": "application/vnd.adobe.adept+xml"}
  logging.info("Sending fullfilment request to {}".format(url))

  ff_reply = send(url, ff_request, args.dry)

  if args.dry:
    return
 
  try: 
    title, ebook_url, license_token = parse_fulfillment_reply(ff_reply)
  except Exception:
    logging.error("Error while parsing fulfillment reply: ".format(ff_reply))
    return

  # Get epub URL and download it
  logging.info("Downloading {} from {} ...".format(title, ebook_url))
  try:
    r = requests.get(ebook_url)
    r.raise_for_status()
    epub = r.content
  except Exception:
    logging.error("Error during download phase when targeting {}".format(url))
    return

  # A file containing the license token must be added to the epub
  logging.info("Patching epub ...")
  try:
    patched_epub = patch_epub.patch(epub, license_token)
  except Exception as e:
    logging.error("Could not patch epub: {}".format(e.message))
    return

  # Write file to disc
  # TODO: configurable output ?
  filename = "{0}.epub".format(title)
  logging.info("Writing {} ...".format(filename))
  try:
    with open(filename, "w") as epub_file:
      epub_file.write(patched_epub)
  except Exception as e:
    logging.error("Could not write file {}: {}".format(filename, e.message))
    return

  logging.info("Successfully downloaded file {}".format(filename))
