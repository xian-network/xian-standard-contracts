import unittest
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.hashing import sha3
from contracting.client import ContractingClient
from xian_py.wallet import Wallet
from pathlib import Path
import datetime

class TestCurrencyContract(unittest.TestCase):
    def setUp(self):

        self.chain_id = "test-chain"
        self.environment = {
            "chain_id": self.chain_id
        }

        # Called before every test, bootstraps the environment.
        self.client = ContractingClient(environment=self.environment)
        self.client.flush()

            # Get the directory containing the test file
        current_dir = Path(__file__).parent
        # Navigate to the contract file in the parent directory
        contract_path = current_dir.parent / "XSC0002.py"
        
        with open(contract_path) as f:
            code = f.read()
            self.client.submit(code, name="currency")

        self.currency = self.client.get_contract("currency")

    def tearDown(self):
        self.environment = {
            "chain_id": self.chain_id
        }
        # Called after every test, ensures each test starts with a clean slate and is isolated from others
        self.client.flush()

    def test_initial_balance(self):
        # Check initial balance set by constructor
        sys_balance = self.currency.balances["sys"]
        self.assertEqual(sys_balance, 1_000_000)

    def test_transfer(self):
        # Setup
        self.currency.transfer(amount=100, to="bob", signer="sys")
        self.assertEqual(self.currency.balances["bob"], 100)
        self.assertEqual(self.currency.balances["sys"], 999_900)

    def test_change_metadata(self):
        # Only the operator should be able to change metadata
        with self.assertRaises(Exception):
            self.currency.change_metadata(
                key="token_name", value="NEW TOKEN", signer="bob"
            )
        # Operator changes metadata
        self.currency.change_metadata(key="token_name", value="NEW TOKEN", signer="sys")
        new_name = self.currency.metadata["token_name"]
        self.assertEqual(new_name, "NEW TOKEN")

    def test_approve_and_allowance(self):
        # Test approve
        self.currency.approve(amount=500, to="eve", signer="sys")
        # Test allowance
        allowance = self.currency.approvals["sys", "eve"]
        self.assertEqual(allowance, 500)

    def test_transfer_from_without_approval(self):
        # Attempt to transfer without approval should fail
        with self.assertRaises(Exception):
            self.currency.transfer_from(
                amount=100, to="bob", main_account="sys", signer="bob"
            )

    def test_transfer_from_with_approval(self):
        # Setup - approve first
        self.currency.approve(amount=200, to="bob", signer="sys")
        # Now transfer
        self.currency.transfer_from(
            amount=100, to="bob", main_account="sys", signer="bob"
        )
        self.assertEqual(self.currency.balances["bob"], 100)
        self.assertEqual(self.currency.balances["sys"], 999_900)
        remaining_allowance = self.currency.approvals["sys", "bob"]
        self.assertEqual(remaining_allowance, 100)


    # XST002 / Permit Tests


    # Helper Functions

    def fund_wallet(self, funder, spender, amount):
        self.currency.transfer(amount=100, to=spender, signer=funder)


    def construct_permit_msg(self, owner: str, spender: str, value: float, deadline: dict):
        return f"{owner}:{spender}:{value}:{deadline}:currency:{self.chain_id}"


    def create_deadline(self, minutes=1):
        d = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        return Datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute)
    

    # Permit Tests

    def test_permit_valid(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        hash = sha3(msg)
        signature = wallet.sign_msg(msg)
        # WHEN
        response = self.currency.permit(owner=public_key, spender=spender, value=value, deadline=str(deadline), signature=signature)
        # THEN
        self.assertEqual(response, hash)


    def test_permit_expired(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline(minutes=-1)  # Past deadline
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg)
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=str(deadline), signature=signature)
        # THEN
        self.assertIn('Permit has expired', str(context.exception))


    def test_permit_invalid_signature(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg + "tampered")
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=str(deadline), signature=signature)
        # THEN
        self.assertIn('Invalid signature', str(context.exception))


    def test_permit_double_spending(self):
        # GIVEN
        private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
        wallet = Wallet(private_key)
        public_key = wallet.public_key
        deadline = self.create_deadline()
        spender = "some_spender"
        value = 100
        msg = self.construct_permit_msg(public_key, spender, value, deadline)
        signature = wallet.sign_msg(msg)
        self.currency.permit(owner=public_key, spender=spender, value=value, deadline=str(deadline), signature=signature)
        # WHEN
        with self.assertRaises(Exception) as context:
            self.currency.permit(owner=public_key, spender=spender, value=value, deadline=str(deadline), signature=signature)
        # THEN
        self.assertIn('Permit can only be used once', str(context.exception))
        

    def test_approve_overwrites_previous_allowance(self):
        # GIVEN an initial approval setup
        self.currency.approve(amount=500, to="eve", signer="sys")
        initial_allowance = self.currency.approvals["sys", "eve"]
        self.assertEqual(initial_allowance, 500)
        
        # WHEN a new approval is made
        self.currency.approve(amount=200, to="eve", signer="sys")
        new_allowance = self.currency.approvals["sys", "eve"]
        
        # THEN the new allowance should overwrite the old one
        self.assertEqual(new_allowance, 200)
        
    def test_permit_overwrites_previous_allowance(self):
            # GIVEN an initial allowance setup
            private_key = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
            wallet = Wallet(private_key)
            public_key = wallet.public_key
            spender = "some_spender"
            initial_value = 500
            new_value = 200
            deadline = str(self.create_deadline())
            
            # Set initial allowance via permit
            msg = self.construct_permit_msg(public_key, spender, initial_value, deadline)
            signature = wallet.sign_msg(msg)
            self.currency.permit(owner=public_key, spender=spender, value=initial_value, deadline=deadline, signature=signature)
            
            # Verify initial allowance
            initial_allowance = self.currency.approvals[public_key, spender]
            self.assertEqual(initial_allowance, initial_value)
            
            # WHEN a new permit is granted
            msg = self.construct_permit_msg(public_key, spender, new_value, deadline)
            signature = wallet.sign_msg(msg)
            self.currency.permit(owner=public_key, spender=spender, value=new_value, deadline=deadline, signature=signature)
            
            # THEN the new allowance should overwrite the old one
            new_allowance = self.currency.approvals[public_key, spender]
            self.assertEqual(new_allowance, new_value)




if __name__ == "__main__":
    unittest.main()
