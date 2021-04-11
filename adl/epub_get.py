import logging
import requests
from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, sign_xml, add_subelement, get_error
import utils
import patch_epub
import account
import base64

from api_call import FFAuth, InitLicense, Fulfillment

def parse_acsm(acsm_filename):
  fftoken = etree.parse(acsm_filename)
  token_root = fftoken.getroot()

  operator = token_root.find("{http://ns.adobe.com/adept}operatorURL").text

  return operator, token_root

def log_in(config, acc, operator, dry_mode):
  ffauth = FFAuth(operator, acc, config)
  result = ffauth.call(dry_mode)

  if dry_mode or result:
    init_license = InitLicense(operator, acc)
    result = init_license.call(dry_mode)
    return dry_mode or result
  else:
    logging.info(get_error(reply))
    return False

def get_ebook(args, data):
  logging.info("Opening {} ...".format(args.filename))

  a = data.get_current_account()
  if a is None:
    logging.error("Please log in with a user and select it first")
    return

  # The ACSM file contains a "fulfillment URL" that we must query
  # in order to get the real file URL
  operator, acsm_content = parse_acsm(args.filename)

  if not log_in(data.config, a, operator, args.dry):
    logging.info("Failed to init license")
    return

  logging.info("Sending fullfilment request to {}".format(url))
  try: 
    ff = Fulfillment(acsm_content, a, operator)
    title, ebook_url, license_token = ff.call(args.dry)
  except Exception:
    logging.exception("Error during fulfillment")
    return

  if args.dry:
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
