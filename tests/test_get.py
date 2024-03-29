from context import epub_get, account, db, utils, device, xml_tools, patch_epub, data, bom
from unittest.mock import patch, MagicMock, call, mock_open

import unittest
from lxml import etree

class TestGet(unittest.TestCase):
  def test_gen_rights(self):
    license_token = etree.Element("licenseToken")
    license_token.text = "toto"
    rights_xml = epub_get.generate_rights_xml(license_token)

    expected = b'<?xml version="1.0"?>\n<rights xmlns="http://ns.adobe.com/adept"><licenseToken>toto</licenseToken><licenseServiceInfo><licenseURL>https://nasigningservice.adobe.com/licensesign</licenseURL><certificate>MIIEvjCCA6agAwIBAgIER2q5ljANBgkqhkiG9w0BAQUFADCBhDELMAkGA1UEBhMCVVMxIzAhBgNVBAoTGkFkb2JlIFN5c3RlbXMgSW5jb3Jwb3JhdGVkMRswGQYDVQQLExJEaWdpdGFsIFB1Ymxpc2hpbmcxMzAxBgNVBAMTKkFkb2JlIENvbnRlbnQgU2VydmVyIENlcnRpZmljYXRlIEF1dGhvcml0eTAeFw0wODA4MTExNjMzNDhaFw0xMzA4MTEwNzAwMDBaMIGIMQswCQYDVQQGEwJVUzEjMCEGA1UEChMaQWRvYmUgU3lzdGVtcyBJbmNvcnBvcmF0ZWQxGzAZBgNVBAsTEkRpZ2l0YWwgUHVibGlzaGluZzE3MDUGA1UEAxMuaHR0cHM6Ly9uYXNpZ25pbmdzZXJ2aWNlLmFkb2JlLmNvbS9saWNlbnNlc2lnbjCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAs9GRZ1f5UTRySgZ2xAL7TaDKQBfdpIS9ei9Orica0N72BB/WE+82G5lfsZ2HdeCFDZG/oz2WPLXovcuUAbFKSIXVLyc7ONOd4sczeXQYPixeAvqzGtsyMArIzaeJcriGVPRnbD/spbuHR0BHhJEakIiDtQLJz+xgVYHlicx2H/kCAwEAAaOCAbQwggGwMAsGA1UdDwQEAwIFoDBYBglghkgBhvprHgEESwxJVGhlIHByaXZhdGUga2V5IGNvcnJlc3BvbmRpbmcgdG8gdGhpcyBjZXJ0aWZpY2F0ZSBtYXkgaGF2ZSBiZWVuIGV4cG9ydGVkLjAUBgNVHSUEDTALBgkqhkiG9y8CAQIwgbIGA1UdIASBqjCBpzCBpAYJKoZIhvcvAQIDMIGWMIGTBggrBgEFBQcCAjCBhhqBg1lvdSBhcmUgbm90IHBlcm1pdHRlZCB0byB1c2UgdGhpcyBMaWNlbnNlIENlcnRpZmljYXRlIGV4Y2VwdCBhcyBwZXJtaXR0ZWQgYnkgdGhlIGxpY2Vuc2UgYWdyZWVtZW50IGFjY29tcGFueWluZyB0aGUgQWRvYmUgc29mdHdhcmUuMDEGA1UdHwQqMCgwJqAkoCKGIGh0dHA6Ly9jcmwuYWRvYmUuY29tL2Fkb2JlQ1MuY3JsMB8GA1UdIwQYMBaAFIvu8IFgyaLaHg5SwVgMBLBD94/oMB0GA1UdDgQWBBSQ5K+bvggI6Rbh2u9nPhH8bcYTITAJBgNVHRMEAjAAMA0GCSqGSIb3DQEBBQUAA4IBAQC0l1L+BRCccZdb2d9zQBJ7JHkXWt1x/dUydU9I/na+QPFE5x+fGK4cRwaIfp6fNviGyvtJ6Wnxe6du/wlarC1o26UNpyWpnAltcy47LpVXsmcV5rUlhBx10l4lecuX0nx8/xF8joRz2BvvAusK+kxgKeiAjJg2W20wbJKh0Otct1ZihruQsEtGbZJ1L55xfNhrm6CKAHuGuTDYQ/S6W20dUaDUiNFhA2n2eEySLwUwgOuuhfVUPb8amQQKbF4rOQ2rdjAskEl/0CiavW6Xv0LGihThf6CjEbNSdy+vXQ7K9wFbKsE843DflpuSPfj2Aagtyrv/j1HsBjsf03e0uVu5</certificate></licenseServiceInfo></rights>'
    self.assertEqual(rights_xml, expected)

  def test_parse_acsm(self):
    operator, _ = epub_get.parse_acsm("files/fake.acsm")
    self.assertEqual(operator, "https://acs4.kobo.com/fulfillment")

  def test_login(self):
    d = bom.Device()
    d.device_key = 1
    d.name = "local"

    a = bom.Account()
    a.urn = "toto"
    a.licenseCertificate = b"LICENSECERT"
    a.devices = [d]

    c = bom.Config()
    c.current_user = "toto"
    c.authentication_certificate = b"AUTHCERT"

    data.config = c
    data.accounts = [a]

    backup = utils.extract_cert_from_pkcs12, utils.extract_pk_from_pkcs12, xml_tools.generate_signature, utils.make_nonce, utils.get_expiration_date
    utils.extract_cert_from_pkcs12 = MagicMock(return_value=b"DEADBEEF")
    utils.extract_pk_from_pkcs12 = MagicMock(return_value="DEADBEEF")
    utils.make_nonce = MagicMock(return_value="11Mo2AAAAAA=")
    utils.get_expiration_date = MagicMock(return_value="2021-04-15T23:27:34-00:00")
    xml_tools.generate_signature = MagicMock(return_value="0123456789ABCDEF")

    with patch('requests.post') as mock_request:
      mock_request.return_value.status_code = 200
      mock_request.return_value.text = "success"

      epub_get.log_in(c, a, "http://fairyland.com")

      auth_call = call('http://fairyland.com/Auth', data=b'<credentials xmlns="http://ns.adobe.com/adept"><user>toto</user><certificate>REVBREJFRUY=</certificate><licenseCertificate>LICENSECERT</licenseCertificate><authenticationCertificate>AUTHCERT</authenticationCertificate></credentials>', headers={'Content-type': 'application/vnd.adobe.adept+xml', 'charset': 'utf-8'})
      initlicense_call = call('http://adeactivate.adobe.com/adept/InitLicenseService', data=b'<licenseServiceRequest xmlns="http://ns.adobe.com/adept" identity="user"><operatorURL>http://fairyland.com</operatorURL><nonce>11Mo2AAAAAA=</nonce><expiration>2021-04-15T23:27:34-00:00</expiration><user>toto</user><signature>0123456789ABCDEF</signature></licenseServiceRequest>', headers={'Content-type': 'application/vnd.adobe.adept+xml', 'charset': 'utf-8'})
      rfs = call().raise_for_status()
      mock_request.assert_has_calls([auth_call, rfs, initlicense_call, rfs])


    utils.extract_cert_from_pkcs12, utils.extract_pk_from_pkcs12, xml_tools.generate_signature, utils.make_nonce, utils.get_expiration_date = backup

  def test_fulfillment(self):
    d = bom.Device()
    d.device_id = "urn:1"
    d.device_type = "mobile"
    d.device_key = 1
    d.name = "local"

    a = bom.Account()
    a.urn = "toto"
    a.devices = [d]

    operator = "http://fairyland.com"
    content = etree.Element("Content")

    backup = utils.extract_pk_from_pkcs12, xml_tools.generate_signature
    utils.extract_pk_from_pkcs12 = MagicMock(return_value="DEADBEEF")
    xml_tools.generate_signature = MagicMock(return_value="0123456789ABCDEF")
    
    with patch('requests.post') as mock_request:
      mock_request.return_value.status_code = 200
      mock_request.return_value.text = '<fulfillment><fulfillmentResult xmlns="http://ns.adobe.com/adept"><resourceItemInfo xmlns="http://ns.adobe.com/adept"><licenseToken>toto</licenseToken><src>http://books.com/mybook.epub</src><metadata><title xmlns="http://purl.org/dc/elements/1.1/">My great book</title></metadata></resourceItemInfo></fulfillmentResult></fulfillment>'

      title, url, licenseToken = epub_get.fulfill(content, a, operator)

      self.assertEqual(title, "My great book")
      self.assertEqual(url, "http://books.com/mybook.epub")
      self.assertEqual(etree.tostring(licenseToken), b'<licenseToken xmlns="http://ns.adobe.com/adept">toto</licenseToken>')

    utils.extract_pk_from_pkcs12, xml_tools.generate_signature = backup

  def test_get(self):
    d = bom.Device()
    d.name = "local"

    a = bom.Account()
    a.urn = "toto"
    a.devices = [d]

    c = bom.Config()
    c.current_user = "toto"

    data.config = c
    data.accounts = [a]

    filename = 'files/fake.acsm'

    license_token = etree.Element("licenseToken")
    license_token.text = "toto"

    backup = epub_get.log_in, epub_get.fulfill, epub_get.generate_rights_xml, patch_epub.patch 
    epub_content = 'Zipped book content'
    rights_content = "<rights>GOD</rights>"
    book_title = "Book Title"

    epub_get.log_in = MagicMock(return_value=True)
    epub_get.fulfill = MagicMock(return_value=(book_title, "http://books.com/mybook.epub", license_token))
    epub_get.generate_rights_xml = MagicMock(return_value=rights_content)
    patch_epub.patch = MagicMock(return_value = "{}{}".format(epub_content, rights_content))

    with patch('requests.get') as mock_request:
      mock_request.return_value.status_code = 200
      mock_request.return_value.text = epub_content
      
      with patch('builtins.open', mock_open()) as mo:
        epub_get.get_ebook(filename)
        mo.assert_called_with("{}.epub".format(book_title), 'wb')
        mo().write.assert_called_with("{}{}".format(epub_content, rights_content))
    
      mock_request.assert_called_with('http://books.com/mybook.epub')
    epub_get.log_in, epub_get.fulfill, epub_get.generate_rights_xml, patch_epub.patch = backup
  

if __name__ == '__main__':
  unittest.main()
