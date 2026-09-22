# Base borrower / migration blocker audit

Pinned Base block: **51,135,337**. Debt evaluated on the local fork at **51,156,937**, after the simulated registry timelock. Not a current live balance quote.

Checked all **56 borrowers**, with no read errors, and **405 funded depositors** for account locks.

Amounts below are exact decimal conversions. Debt and borrowing capacity are in GREEN; collateral value is the CreditEngine's USD value, not the total market value of every deposit. A failed borrowing-LTV check does not by itself imply liquidation eligibility.

Accounts with no funded positions have debt-health issues but no deposited position to migrate. This is exhaustive for the scanned debt-health/account-lock conditions, not every possible migration error.

## 0xbA49a3d456de4e670a94E13b8b1E5315929C97Ad

- Current debt: **0.406945383565583791 GREEN**
- Principal: 0.387616337112982852 GREEN
- Borrowing capacity: 0.406924993016601834 GREEN
- Debt above capacity: 0.000020390548981957 GREEN
- Eligible collateral value: $0.508656241270752293
- Account locked: False; stored liquidation flag: False

| Vault | Asset | Deposited amount | Token address |
| --- | --- | ---: | --- |
| 5 | undyUSDC | 0.501337 | `0x99e65176F7FA8743E3fbaEF277d1Da448e361367` |

Isolated ordinary migration: **blocked** (see JSON for the call trace).

## 0xD7A48E684Da48cc384fD80bb1Fed7D8970bfe91b

- Current debt: **0.982796745232664627 GREEN**
- Principal: 0.982796745232664627 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.982796745232664627 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

**No funded vault positions in the reconciled census.**

## 0xE5aB77408c25E7C1562C09067A8Fa3d0C00ac999

- Current debt: **0.126807288588630824 GREEN**
- Principal: 0.126807288588630824 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.126807288588630824 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

**No funded vault positions in the reconciled census.**

## 0x28E2b238a3a7634C6C7e23b895790505B1C31Cd0

- Current debt: **295.390359294423333333 GREEN**
- Principal: 291.8436439866823512 GREEN
- Borrowing capacity: 294.803201016421243158 GREEN
- Debt above capacity: 0.587158278002090175 GREEN
- Eligible collateral value: $368.504001270526553948
- Account locked: False; stored liquidation flag: False

| Vault | Asset | Deposited amount | Token address |
| --- | --- | ---: | --- |
| 1 | sGREEN | 268.343998732271985495 | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |
| 2 | RIPE | 686.115358927338975876 | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` |
| 5 | undyUSDC | 363.201462 | `0x99e65176F7FA8743E3fbaEF277d1Da448e361367` |

Isolated RipeGov migration reverted: **True**.
## 0xd060D0C2bbd34AB116bd6c917147B560C66F875b

- Current debt: **0.068260520361387739 GREEN**
- Principal: 0.068260520361387739 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.068260520361387739 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

**No funded vault positions in the reconciled census.**

## 0x6b34e50bDfC20A0869BF28249bac24d12Cc3fbbd

- Current debt: **0.02290593604231681 GREEN**
- Principal: 0.02290593604231681 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.02290593604231681 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

**No funded vault positions in the reconciled census.**

## 0x465e1D1e73Ad725434a4ABe12eaa60C7A7ab792E

- Current debt: **0.257547140184901938 GREEN**
- Principal: 0.257547140184901938 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.257547140184901938 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

| Vault | Asset | Deposited amount | Token address |
| --- | --- | ---: | --- |
| 2 | RIPE | 2.691899099855195626 | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` |

Isolated RipeGov migration reverted: **True**.

## 0xda67c6423FCD8aBEa9A02Ef515EdfB62880D2738

- Current debt: **0.013700809940108052 GREEN**
- Principal: 0.013700809940108052 GREEN
- Borrowing capacity: 0 GREEN
- Debt above capacity: 0.013700809940108052 GREEN
- Eligible collateral value: $0
- Account locked: False; stored liquidation flag: True

| Vault | Asset | Deposited amount | Token address |
| --- | --- | ---: | --- |
| 2 | RIPE | 51.075203846727171346 | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` |

Isolated RipeGov migration reverted: **True**.
