balances = Hash(default_value=0)
approvals = Hash(default_value=0)
metadata = Hash()

minter = Variable()


TransferEvent = LogEvent(
    event="Transfer",
    params={
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": (int, float, decimal)},
    },
)
ApproveEvent = LogEvent(
    event="Approve",
    params={
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": (int, float, decimal)},
    },
)
MintEvent = LogEvent(
    event="Mint",
    params={
        "to": {"type": str, "idx": True},
        "amount": {"type": (int, float, decimal)},
    },
)
BurnEvent = LogEvent(
    event="Burn",
    params={
        "from": {"type": str, "idx": True},
        "amount": {"type": (int, float, decimal)},
    },
)

@construct
def seed():
    balances[ctx.caller] = 1_000_000

    metadata["token_name"] = "TEST TOKEN"
    metadata["token_symbol"] = "TST"
    metadata["token_logo_url"] = "https://some.token.url/test-token.png"
    metadata["token_website"] = "https://some.token.url"
    metadata["total_supply"] = balances[ctx.caller]
    metadata["operator"] = ctx.caller

    minter.set(ctx.caller)


@export
def change_metadata(key: str, value: Any):
    assert ctx.caller == metadata["operator"], "Only operator can set metadata."
    metadata[key] = value


@export
def transfer(amount: float, to: str):
    assert amount > 0, "Cannot send negative balances."
    assert balances[ctx.caller] >= amount, "Not enough coins to send."

    balances[ctx.caller] -= amount
    balances[to] += amount

    TransferEvent({"from": ctx.caller, "to": to, "amount": amount})


@export
def approve(amount: float, to: str):
    assert amount >= 0, "Cannot approve negative balances."
    approvals[ctx.caller, to] = amount

    ApproveEvent({"from": ctx.caller, "to": to, "amount": amount})


@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, "Cannot send negative balances."
    assert (
        approvals[main_account, ctx.caller] >= amount
    ), f"Not enough coins approved to send. You have {balances[main_account, ctx.caller]} and are trying to spend {amount}"
    assert balances[main_account] >= amount, "Not enough coins to send."

    approvals[main_account, ctx.caller] -= amount
    balances[main_account] -= amount
    balances[to] += amount

    TransferEvent({"from": main_account, "to": to, "amount": amount})


@export
def balance_of(address: str):
    return balances[address]


@export
def change_minter(new_minter: str):
    assert ctx.caller == minter.get(), "Only minter can change minter."
    minter.set(new_minter)


@export
def mint(amount: float, to: str):
    assert ctx.caller == minter.get(), "Only minter can mint tokens."
    assert amount > 0, "Cannot mint negative balances."

    balances[to] += amount
    metadata["total_supply"] += amount

    MintEvent({"to": to, "amount": amount})


@export
def burn(amount: float):
    assert amount > 0, "Cannot burn negative balances."
    assert balances[ctx.caller] >= amount, "Not enough coins to burn."

    balances[ctx.caller] -= amount
    metadata["total_supply"] -= amount

    BurnEvent({"from": ctx.caller, "amount": amount})
