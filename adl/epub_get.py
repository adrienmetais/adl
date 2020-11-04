import logging
import requests
from lxml import etree

from xml_tools import ADEPT_NS, NSMAP, sign_xml
import patch_epub

def build_fulfillment_request(acsm_filename, config):
  ff = etree.Element("{%s}fulfill" % ADEPT_NS, nsmap=NSMAP)

  user = etree.Element("user")
  user.text = config.get("user", "id")
  ff.append(user)

  device = etree.Element("device")
  device.text = config.get("device", "id")
  ff.append(device)

  deviceType = etree.Element("deviceType")
  deviceType.text = config.get("device", "type")
  ff.append(deviceType)

  fftoken = etree.parse(acsm_filename)
  token_root = fftoken.getroot()

  ff.append(token_root)

  ff = sign_xml(ff)

  operator = token_root.find("{http://ns.adobe.com/adept}operatorURL").text
  
  return (operator, etree.tostring(ff))

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

  # The ACSM file contains a "fulfillment URL" that we must query
  # in order to get the real file URL
  operator, ff_request = build_fulfillment_request(args.filename, config)

  url = "{0}/Fulfill".format(operator)
  headers = {"Content-type": "application/vnd.adobe.adept+xml"}
  logging.info("Sending fullfilment request to {}".format(url))
  logging.debug(ff_request)

  if args.dry:
    print(ff_request)
    print("(Dry run - Not sent)")
    return 

  try:
    # Send the fulfillment request
    r = requests.post(url, data=ff_request, headers=headers)
    r.raise_for_status()
    ff_reply = r.text
  except Exception:
    logging.error("Error during fulfillment phase when targeting {}".format(url))
    return

  logging.debug(ff_reply)
 
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

  print("Successfully downloaded file", filename)
