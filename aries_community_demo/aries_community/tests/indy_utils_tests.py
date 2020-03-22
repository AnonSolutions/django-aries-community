from django.test import TestCase

from ..indy_utils import *


TEST_SEED = "12345678901234567890123456789012"
TEST_DID  = "6sYe1y3zXhmyrBkgHgAgaq"

class IndyUtilsTests(TestCase):

    def test_seed_to_did(self):
        (did, verkey) = seed_to_did(TEST_SEED)

        assert did == TEST_DID

