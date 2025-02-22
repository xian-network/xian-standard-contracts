# XSC004 Wrapped Token Contract

The **XSC004** contract is a specialized token contract for representing tokens from another chain ("wrapped" tokens) on the Xian blockchain. This contract provides the standard token functionalities—such as transfers, approvals, and metadata management—while adding **mint** and **burn** capabilities for the purpose of wrapping or unwrapping tokens that originate from a different blockchain.

## Overview

When tokens from an external chain are deposited into a bridge or custody solution, the **XSC004** contract can “mint” corresponding wrapped tokens on the Xian blockchain. Conversely, when users want to withdraw their tokens back to the original chain, those wrapped tokens are “burned” on Xian, and the original tokens are released on the external chain.

The contract includes:

- A **minter** role (which can be assigned to either a wallet address or another contract) that controls the minting of new wrapped tokens.
- A **burn** function, enabling token holders to unwrap and destroy the wrapped tokens on Xian.
- Standard token operations (`transfer`, `approve`, `transfer_from`) for fungible tokens.
- Metadata management for storing and updating token details.

## Contract Functions

### 1. `seed()`

Initializes the contract’s state on deployment:

- Assigns an initial token balance to the contract creator.
- Stores basic token metadata (`token_name`, `token_symbol`, `token_logo_url`, `token_website`, `operator`).
- Sets the `minter` variable to the contract creator.

No parameters; called once during contract deployment.

---

### 2. `change_metadata(key: str, value: Any)`

Updates the token metadata. Only the operator (stored in `metadata["operator"]`) can call this function.

**Parameters:**
- `key`: The metadata key to update (e.g., `"token_name"`).
- `value`: The new value to store for that key.

---

### 3. `transfer(amount: float, to: str)`

Moves tokens from the caller’s balance to another address.

**Parameters:**
- `amount`: Number of tokens to transfer (must be positive).
- `to`: Address of the recipient.

---

### 4. `approve(amount: float, to: str)`

Allows the caller (token holder) to approve another account to transfer up to `amount` tokens on their behalf.

**Parameters:**
- `amount`: The approved number of tokens (must be non-negative).
- `to`: The account authorized to spend tokens on behalf of the caller.

---

### 5. `transfer_from(amount: float, to: str, main_account: str)`

Executes a transfer on behalf of `main_account`, as long as the caller has been approved via [`approve`](#4-approveamount-float-to-str).

**Parameters:**
- `amount`: Number of tokens to transfer (must be positive).
- `to`: Recipient address.
- `main_account`: Address of the token holder who granted the approval.

---

### 6. `balance_of(address: str)`

Returns the balance of a given address.

**Parameters:**
- `address`: The address whose balance is being queried.

**Returns:**
- Current token balance of `address`.

---

### 7. `change_minter(new_minter: str)`

Changes the `minter` role to another address or contract. Only the current minter can call this function.

**Parameters:**
- `new_minter`: The address or contract that will become the new minter.

---

### 8. `mint(amount: float, to: str)`

Mints (creates) new tokens on the Xian chain, increasing the total supply. Used to “wrap” tokens when they are locked or deposited in a corresponding bridge on the original chain.

**Parameters:**
- `amount`: Number of tokens to mint (must be positive).
- `to`: Address that will receive the newly minted tokens.

**Notes:**
- Only the current minter can call this function.

---

### 9. `burn(amount: float)`

Burns (destroys) the caller’s tokens, decreasing the total supply. Used to “unwrap” tokens when returning them to the original chain.

**Parameters:**
- `amount`: Number of tokens to burn (must be positive).

---

## Events

The contract emits the following events to the log for external tracking and auditing:

- **TransferEvent**: Fired whenever tokens are transferred (via `transfer` or `transfer_from`).
- **ApproveEvent**: Fired whenever a token approval is set (via `approve`).
- **MintEvent**: Fired whenever new tokens are minted (via `mint`).
- **BurnEvent**: Fired whenever tokens are burned (via `burn`).

## Usage Scenarios

1. **Initial Deployment and Seeding**  
   - The contract deployer calls `seed()` to set up the initial state, assign themselves tokens, and configure metadata.
   - The deployer is automatically the first `minter`.

2. **Wrapping Tokens**  
   - A bridge or custody solution locks tokens from the external chain.  
   - The bridge calls `mint()` on the Xian chain, creating an equivalent number of wrapped tokens in the user’s address.

3. **Transferring Wrapped Tokens**  
   - Holders of wrapped tokens can freely transfer them or use `approve/transfer_from` to participate in DeFi or other DApps on the Xian chain.

4. **Unwrapping Tokens**  
   - The holder calls `burn()` to destroy their wrapped tokens on Xian.  
   - The bridge on the other chain detects the burn event and releases or unlocks the original tokens to the holder’s address on the external chain.

## Contact

For questions, feedback, or technical support regarding the **XSC004 Wrapped Token Contract**, please open an issue in the official repository or reach out to the Xian project maintainers. We appreciate your interest in bringing interoperable assets to the Xian blockchain!
