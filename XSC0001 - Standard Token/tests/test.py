import unittest
from contracting.client import ContractingClient


class TestCurrencyContract(unittest.TestCase):
    def setUp(self):
        # Called before every test, bootstraps the environment.
        self.client = ContractingClient()
        self.client.flush()

        with open("token_xsc003.py") as f:
            code = f.read()
            self.client.submit(code, name="currency")

        self.currency = self.client.get_contract("currency")

    def tearDown(self):
        # Called after every test, ensures each test starts with a clean slate and is isolated from others
        self.client.flush()

    def test_balance_of(self):
        # GIVEN
        receiver = 'receiver_account'
        self.currency.balances[receiver] = 100000000000000

        # WHEN
        balance = self.currency.balance_of(address=receiver, signer="sys")

        # THEN
        self.assertEqual(balance, 100000000000000)

    def test_initial_balance(self):
        # GIVEN the initial setup
        # WHEN checking the initial balance
        sys_balance = self.currency.balances["sys"]
        # THEN the balance should be as expected
        self.assertEqual(sys_balance, 1_000_000)

    def test_transfer(self):
        # GIVEN a transfer setup
        self.currency.transfer(amount=100, to="bob", signer="sys")
        # WHEN checking balances after transfer
        bob_balance = self.currency.balances["bob"]
        sys_balance = self.currency.balances["sys"]
        # THEN the balances should reflect the transfer correctly
        self.assertEqual(bob_balance, 100)
        self.assertEqual(sys_balance, 999_900)

    def test_change_metadata(self):
        # GIVEN a non-operator trying to change metadata
        with self.assertRaises(Exception):
            self.currency.change_metadata(
                key="token_name", value="NEW TOKEN", signer="bob"
            )
        # WHEN the operator changes metadata
        self.currency.change_metadata(key="token_name", value="NEW TOKEN", signer="sys")
        new_name = self.currency.metadata["token_name"]
        # THEN the metadata should be updated correctly
        self.assertEqual(new_name, "NEW TOKEN")

    def test_approve_and_allowance(self):
        # GIVEN an approval setup
        self.currency.approve(amount=500, to="eve", signer="sys")
        # WHEN checking the allowance
        allowance = self.currency.balances["sys", "eve"]
        # THEN the allowance should be set correctly
        self.assertEqual(allowance, 500)

    def test_transfer_from_without_approval(self):
        # GIVEN an attempt to transfer without approval
        # WHEN the transfer is attempted
        # THEN it should fail
        with self.assertRaises(Exception):
            self.currency.transfer_from(
                amount=100, to="bob", main_account="sys", signer="bob"
            )

    def test_transfer_from_with_approval(self):
        # GIVEN a setup with approval
        self.currency.approve(amount=200, to="bob", signer="sys")
        # WHEN transferring with approval
        self.currency.transfer_from(
            amount=100, to="bob", main_account="sys", signer="bob"
        )
        bob_balance = self.currency.balances["bob"]
        sys_balance = self.currency.balances["sys"]
        remaining_allowance = self.currency.balances["sys", "bob"]
        # THEN the balances and allowance should reflect the transfer
        self.assertEqual(bob_balance, 100)
        self.assertEqual(sys_balance, 999_900)
        self.assertEqual(remaining_allowance, 100)

if __name__ == "__main__":
    unittest.main()
