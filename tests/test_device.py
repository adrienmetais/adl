from context import account, utils, login, device, db, api_call
from mock import patch, MagicMock, Mock, mock_open
import unittest
import base64
import argparse
import os

class TestDevice(unittest.TestCase):
  def test_build_activation_file(self):
    expected = '<activationInfo xmlns="http://ns.adobe.com/adept"><activationServiceInfo><authURL>authurl</authURL><userInfoURL>userinfourl</userInfoURL><activationURL>authurl</activationURL><certificate>ACT_CERTIFICATE</certificate></activationServiceInfo><credentials><user>toto</user><licenseCertificate/><privateLicenseKey>SuperSecretKey</privateLicenseKey><authenticationCertificate>AUTH_CERTIFICATE</authenticationCertificate><username method="AdobeID">toto@adobe.com</username></credentials><activationToken/></activationInfo>'

    default_account = account.Account()
    default_account.urn = "toto"
    default_account.sign_id = "toto@adobe.com"
    default_account.sign_method = "AdobeID"
    default_account.get_private_key = MagicMock(return_value="SuperSecretKey")

    activationToken = "<activationToken></activationToken>"

    conf = account.Config()
    conf.auth_url = 'authurl'
    conf.userinfo_url = 'userinfourl'
    conf.activation_certificate = 'ACT_CERTIFICATE'
    conf.authentication_certificate = 'AUTH_CERTIFICATE'

    content = device.build_activation_file(default_account, activationToken, conf)

    self.assertEqual(content, expected)    

  def test_read_device_file(self):
    d = device.read_device_file("./fake_device")
    self.assertEqual(d.name, "Cybook Gen3")
    self.assertEqual(d.type, "tethered")
    self.assertEqual(d.fingerprint, "MDgwOTI2MDE0MjA2MDA3NjUzYQA=")

    d = device.read_device_file("./fake_fake_device")
    self.assertIsNone(d)

  def test_read_activation_file(self):
    username, plk, device_id = device.read_activation_file("./fake_device")
    self.assertIsNone(username, True)
    self.assertIsNone(plk, True)

  def test_write_activation_file(self):
    content = '<activationInfo xmlns="http://ns.adobe.com/adept"><activationServiceInfo><authURL>authurl</authURL><userInfoURL>userinfourl</userInfoURL><activationURL>authurl</activationURL><certificate>ACT_CERTIFICATE</certificate></activationServiceInfo><credentials><user>toto</user><licenseCertificate/><privateLicenseKey>SuperSecretKey</privateLicenseKey><authenticationCertificate>AUTH_CERTIFICATE</authenticationCertificate><username method="AdobeID">toto@adobe.com</username></credentials><activationToken/></activationInfo>'
    with patch("__builtin__.open", mock_open()) as m:
      device.write_activation_file("./fake_device", content)
    m.assert_called_once_with('./fake_device/.adobe-digital-editions/activation.xml', 'w')
    h = m()
    h.write.assert_called_once_with(content)

  def test_activate_device(self):
    # Mock data
    args = argparse.Namespace()
    args.mountpoint = './fake_device'
    args.dry = False

    conf = account.Config()
    conf.auth_url = 'authurl'
    conf.userinfo_url = 'userinfourl'
    conf.activation_certificate = 'ACT_CERTIFICATE'
    conf.authentication_certificate = 'AUTH_CERTIFICATE'
    conf.current_user = "toto"

    default_account = account.Account()
    default_account.urn = "toto"
    default_account.sign_id = "toto@adobe.com"
    default_account.sign_method = "AdobeID"

    data = db.DBData()
    data.config = conf
    data.accounts = [default_account]

    d = device.Device()

    # Mock methods
    backup = device.activate, data.add_device, default_account.get_private_key, device.read_device_file, device.read_activation_file, device.build_activation_file, device.write_activation_file

    device.activate = MagicMock(return_value="<activationToken></activationToken>")

    default_account.get_private_key = MagicMock(return_value="SuperSecretKey")
    data.add_device = MagicMock()

    device.read_device_file = MagicMock(return_value=d)
    device.read_activation_file = MagicMock(return_value=(None, None, None))
    device.build_activation_file = MagicMock(return_value="content")
    device.write_activation_file = MagicMock(return_value=True)

    # Test method
    device.device_register(args, data)

    device.read_device_file.assert_called_with(args.mountpoint)
    device.read_activation_file.assert_called_with(args.mountpoint)
    device.build_activation_file.assert_called()
    device.write_activation_file.assert_called_with(args.mountpoint, "content")
    data.add_device.assert_called()

    device.activate.assert_called()

    # restore methods
    device.activate, data.add_device, default_account.get_private_key, device.read_device_file, device.read_activation_file, device.build_activation_file, device.write_activation_file = backup

  def test_activate(self):
    a = account.Account()
    a.pkcs12 = "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"
    d = device.Device()
    d.fingerprint = "dG90bw=="
    d.name = 'local'
    d.device_key = "TlPf+z/dETowaQGk0ZP3NA=="
    a.devices.append(d)
    utils.make_nonce = MagicMock(return_value="0rTl6wAAAAA=")
    utils.get_expiration_date = MagicMock(return_value="2020-11-16T21:47:52-00:00")
    act = api_call.Activate(a, d)
    xml = act.build()
    expected = '<activate xmlns="http://ns.adobe.com/adept" requestType="initial"><fingerprint>dG90bw==</fingerprint><deviceType>standalone</deviceType><clientOS>Windows Vista</clientOS><clientLocale>en</clientLocale><clientVersion>ADE WIN 9,0,1131,27</clientVersion><nonce>0rTl6wAAAAA=</nonce><expiration>2020-11-16T21:47:52-00:00</expiration><user/><signature>GqUb3mNBC9H/OGCINWxrVwlgQlKo0qHMyXppWsQyxmT02R5wKid1Ce8J3gJWWzC0HdRWh9NPxNCdY4WCCN7iBRSCzNAd3S18SqHtLgJdOkhbUJd9t1SaymuLKDfCRXzKBb2IQZj0ue1YGQDNJB7jVSlU9g87MOrIydB6sCaNCYc=</signature></activate>'
    self.assertEqual(xml, expected)

  def test_parse_activation_reply(self):
    d = device.Device()
    act = api_call.Activate(None, d)
    reply = '<activationToken xmlns="http://ns.adobe.com/adept"><device>urn:uuid:a9d8548e-fc74-462a-9551-913ef3b27493</device><fingerprint>yvKBQhD7vweOkx6YVI4pQhhoDn0=</fingerprint><deviceType>standalone</deviceType><activationURL>http://adeactivate.adobe.com/adept</activationURL><user>urn:uuid:06ff762f-e588-4133-8345-b6580dfecd56</user><signature>jWDdUVAbHVsL2oZL25km36VabXO8a8DRQUP0d8PkB2zksnSOk+Sz7T56k29Icxz65SfvfXswx9OkztNP+kHuCpIeK3iXA1U8KWUyQzvPhCpbbvu472A4Sm7bKG3hvoojCRa9/4uqTOn37jRAXozeQYI5sAizMkpgmtHIXH3BGhs=</signature></activationToken>'
    #device_id = device.parse_activation_reply(reply)
    act.parse(reply)
    self.assertEqual(d.device_id, "urn:uuid:a9d8548e-fc74-462a-9551-913ef3b27493")

  
if __name__ == '__main__':
  unittest.main()
