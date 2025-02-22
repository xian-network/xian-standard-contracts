import unittest
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
from contracting.storage.driver import Driver
from contracting.stdlib.bridge.hashing import sha3
from xian_py.wallet import Wallet
from pathlib import Path
import datetime

class TestCurrencyContract(unittest.TestCase):
    def setUp(self):

        # Called before every test, bootstraps the environment.
        self.chain_id = "test-chain"
        self.environment = {
            "chain_id": self.chain_id
        }

        self.client = ContractingClient(environment=self.environment)
        self.client.flush()
        
        # Get the directory containing the test file
        current_dir = Path(__file__).parent
        # Navigate to the contract file in the parent directory
        contract_path = current_dir.parent / "XSC0003.py"

        with open(contract_path) as f:
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
        allowance = self.currency.approvals["sys", "eve"]
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
        remaining_allowance = self.currency.approvals["sys", "bob"]
        # THEN the balances and allowance should reflect the transfer
        self.assertEqual(bob_balance, 100)
        self.assertEqual(sys_balance, 999_900)
        self.assertEqual(remaining_allowance, 100)

    def test_change_minter(self):
        # GIVEN the default minter is 'sys' (from seed)
        # WHEN sys changes the minter to 'new_minter'
        self.currency.change_minter(new_minter="new_minter", signer="sys")
        # THEN the new minter variable should be updated
        self.assertEqual(self.currency.minter.get(), "new_minter")

    def test_change_minter_not_authorized(self):
        # GIVEN an attempt by a non-minter to change the minter
        with self.assertRaises(Exception):
            self.currency.change_minter(new_minter="hacker", signer="bob")

    def test_mint_happy_path(self):
        # GIVEN the default minter is 'sys'
        current_balance = self.currency.balances["alice"]
        current_supply = self.currency.metadata["total_supply"]
        # WHEN the minter mints 500 tokens to 'alice'
        self.currency.mint(amount=500, to="alice", signer="sys")
        # THEN 'alice' balance should increase by 500, total supply should go up by 500
        self.assertEqual(self.currency.balances["alice"], current_balance + 500)
        self.assertEqual(self.currency.metadata["total_supply"], current_supply + 500)

    def test_mint_not_authorized(self):
        # GIVEN an attempt by a non-minter to mint tokens
        with self.assertRaises(Exception):
            self.currency.mint(amount=500, to="bob", signer="bob")

    def test_mint_cannot_be_zero_or_negative(self):
        with self.assertRaises(Exception):
            self.currency.mint(amount=0, to="bob", signer="sys")

        with self.assertRaises(Exception):
            self.currency.mint(amount=-10, to="bob", signer="sys")

    def test_burn_happy_path(self):
        # GIVEN sys has 1,000,000 tokens
        initial_supply = self.currency.metadata["total_supply"]
        initial_balance = self.currency.balances["sys"]
        burn_amount = 1000
        
        # WHEN sys burns 1000 tokens
        self.currency.burn(amount=burn_amount, signer="sys")
        
        # THEN sys's balance and total supply should be reduced
        self.assertEqual(self.currency.balances["sys"], initial_balance - burn_amount)
        self.assertEqual(
            self.currency.metadata["total_supply"], 
            initial_supply - burn_amount
        )

    def test_burn_cannot_be_zero_or_negative(self):
        with self.assertRaises(Exception):
            self.currency.burn(amount=0, signer="sys")

        with self.assertRaises(Exception):
            self.currency.burn(amount=-10, signer="sys")

    def test_burn_more_than_balance(self):
        # GIVEN sys tries to burn more than their current balance
        big_amount = self.currency.balances["sys"] + 1_000_000
        with self.assertRaises(Exception):
            self.currency.burn(amount=big_amount, signer="sys")



if __name__ == "__main__":
    unittest.main()
