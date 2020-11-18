from context import account, utils
from mock import patch, MagicMock
import unittest
import base64
import os

class TestUtils(unittest.TestCase):
  def test_aes_crypt(self):
    ur = os.urandom
    #os.urandom = MagicMock(return_value="0000000000000000")
    os.urandom = MagicMock(return_value=base64.b64decode("2FfII6r4sz2Mgl9QyspUlQ=="))
    cleartext = "MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANpISKWhc8Gh7PYCZzxs7cfzJ+myLiRDRluSVZ1G8S2wxHv0SEkr2HqdCQVfGrU5BrTC5oXmm0hSpewd7Js4mcEgt7fXHeRfNehyroNCEmPsrFL3ZzwKZfnrmSrD5hwJitm5BxDK+jhaolAMUJbIAj17AzcXP+k0Ncw4X5CDnrZ/AgMBAAECgYABUaZ+ubcFWIEiC2msR8w4BRQcqWL1/SITs5Ko3KDgccz+Ir+9EXLBaul/CtASgEG2Heder8IIcddm0dd4KKNlMHziizmi9j1bXPFS7zkujngH46I9cc3no96s1n4Fb6Mmr/BOxgNLT6A3eIRLSnHG2evSTxvGC+FZhuJfm0zAoQJBAPpZNdwmMgXgDXWkNQdywoTJQeX0r+r77jB79Fp7dmT1YiU0Hy8pr1Orn91zTqej/Vu86YeuVPZ3RRWgEYeliDsCQQDfNcKOPq/X1hy78xy+bVk6QTgSqCc+3XnGi/JsvXDagd0DqmcO12/d5SvUguat5nae1vZVVVuTd8zNeqdGuyqNAkEAxi3o3SW/Y7dB8GbVM9g89DD94bQZrsNQg0Ec5qPlzXYTA7CHHya4jFvIad3l3f+LiRu7IpV23MT+A2h7eA4qEQJAaUWUnbvI+TW9VZNiYhl2dLgftwThhY+1CEQmsMxj9lo7H6h1dJV86B1Wn6KhIzFHjsB5a2OXjiR5Tgvj6sMJXQJAUFtke1QJITeobczoI0JdY8RfNMRn6mGNqN1uFkvcu/5/vwhKj7K/zyrSA4hVJ9LKXqxBu7RsFaoHBK5HjU8oyg=="
    devicekey = "7Nc0TFtBePQ2VDSzPJMmWg=="
  
    crypted = utils.aes_crypt(base64.b64decode(cleartext), base64.b64decode(devicekey))
    self.assertEqual(crypted, "2FfII6r4sz2Mgl9QyspUlRaLMLnLX4POPiQJrMI2wxh3p2KCHTODOkRRq0s2FC2WOTUZTMgya0h6P5jg4hh5CYdp3BVOrps80pyzY/l7wGlC1znqkeM3LJzHjW0jTNPdrf+sAXl7g8OmaUWG7Qjd3LW9d69NMbjwUWHuOWGuDjPDnPEyco1SO8siImRVftzoyQbGEzvhwBJvcAZH9vnnc0TBXB1GwZjTsEuFslx+pfNAiBDcKPyilcvEocMgO3LUGsBFylkM8ADJ8NPY4/kCVcvLl+PeCJUtsRebfc3wo8HjyQf7xyDSm0StnSXdccjolp++52YXPNzJXT+S16PobM6KtXaSuxQiFARDLJoBCuHGP/agBRuHwEVIlLU5Ibm7/1Yk2qRtlWdomVnPbzJjJTAXcG3FdqsSXv+pKVBhK0zd8EGhh0DHMmlGQ5kacHpSO1+SEmfqi8UCT5qg+j2eQfv0gkcpBRcD0BcSYRkIo7EA2zn0KCnobqueB36BjdWRNQRf7EXh+Pjqd9wGRQ3tIcGjQb7g3x0upQGE0z8VMy9PlSaHXQ76IhX2XEdhJapWk8O7euailg+l513f1RrKH/z4z0HfO69ajBDaLK68XN+ouiaE2+7JqpBUQA54be5X4hTQRz5mGP+mIVrvWRCqSg/wJyrTo0eSrv10vjwYMvvHGNiq24y4bfs16grM/sxXHO+xNCq7/wlx7rG35bKPoYPf6MBN91b9kDlSdmqHo+XRhVBrXB29cZFIQtKix50UAtMShVPeVYHGRUb04F+nyF6hoRFI6OJsDcIEhFyMQn1RltVcNMopkwbdUWT2DRWGHsxFfl9vLv2Xvg245KXqeK8gs44J+ekMQu5K4Snrfr0=")

    os.urandom = ur

  def test_generate_key(self):
    prvk, pubk = utils.generate_key_pair()
    #print(prvk)
    #print(pubk)

if __name__ == '__main__':
  unittest.main()
