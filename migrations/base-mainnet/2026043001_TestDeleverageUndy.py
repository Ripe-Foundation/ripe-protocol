import boa

from scripts.utils.migration import Migration
from scripts.utils import log


# Captured from /api/alive — Underscore Vault depositors with undy USD debt.
ASSET = "0xb33852cfd0c22647aac501a6af59bc4210a686bf"
VAULT_ID = 5

DELEVERAGE_LIST = [
    ("0x934713d70f639a73ce2184ef7585b89af3d035d7", 20644467557332085941920, 44377050172000000000000),
    ("0x62f9d45c6ce15e7f7c6f379a76f9b4031137b1ae", 10327417066433121100185, 38032745943000000000000),
    ("0xadc22ba025586639b123303ed61b9d4004118c96", 19958152140956169268855, 34695543366000000000000),
    ("0x39fedc7c60cb20d58ed76a77793f9ddc8b70dfdc", 14287671251213175128564, 18860749989000000000000),
    ("0x955af4de9ca03f84c9462457d075acabf1a8afc8",  5322158282887255703656,  6174495229000000000000),
    ("0xf1133e9aef370d8bd8a71abdd64adbb9298b4f4f",  4209948036572067171458,  5133218166000000000000),
    ("0xbb78b430c2020a8655c32aef37bcd1705a82a7b7",  1293589237000000000000,  1293589237000000000000),
    ("0x0e1f4af8f4233db542ac7d858382b30f87c93660",   688949586702848699705,   841217793000000000000),
    ("0xa0ed9ac5878983da938a99f416aadb29d98e778d",    94052006684221375874,   697199989000000000000),
    ("0x381490ff607bb11de75e730ff0698d72573faedb",   401656876000000000000,   401656876000000000000),
    ("0xdbab0b75921e3008fd0bb621a8248d969d2d2f0d",   316836378159301653165,   396572368000000000000),
    ("0xaa4d8996b17387d6bc02203aa520fafcb54e3eab",   277295550730562278324,   355005866000000000000),
    ("0x3bdfde86869874b101466035b57835a087eadc0f",   129710213338727877475,   311221086000000000000),
    ("0x1a9836f6dcc253332ee707bd9808ab3d79d973d5",   311221086000000000000,   311221086000000000000),
    ("0xcffe08bdf20918007f8ab268c32f8756494fc8d8",   311221086000000000000,   311221086000000000000),
    ("0x0e4bd85ed8d2e6b6bb67b39749d2a618fdf78ec0",   167946178182065856889,   205858448000000000000),
    ("0xe7e93730d88bdb7ffd3a18fe10bcac6c44a69de2",   102839212408861308895,   107149891000000000000),
    ("0x81e9a7b73302a339a11f0c0641a0907339b6e8d6",     3135072926633802930,   101396224000000000000),
    ("0x8cb30592b1baf66d7e68f29755654adccc355601",      580077396327688295,   100746732000000000000),
    ("0xe1d299011b61380941b6c193d5e87303defb3759",    79804000445227509653,   100396432000000000000),
    ("0x2f537c2c1d263e66733da492414359b6b70e1269",    52106530613237719173,    99495953000000000000),
    ("0xd8ac9b9f640699c7e6f4464a1a0da629017fe567",    51964583157824739104,    99481910000000000000),
    ("0xb4f6c55b3e51d1ecef78f9c149e4aea7e7ae86a1",      199079772198936762,    78949734000000000000),
    ("0x467ed88cae6a26d9a957531ec1e777f5951a0b58",    31157025952225944753,    78452506000000000000),
    ("0xa1aad70c6c7b24743b15aff3dd6e94b4da180c87",     8235908974880555059,    65500706000000000000),
    ("0xeb080fb93d905fe54d3ad87f7628e6472b5de4f6",    37740828523845747602,    47446418000000000000),
    ("0xc6e4ad3ccdfc65687d2d60a454a8bddc1f4d6c06",    20730881338726641531,    32344059000000000000),
    ("0x7190081341f0e0223e237270b8479159951a5a46",    16105039000000000000,    16105039000000000000),
    ("0x64dd1abdf58f3066095e9240d66986fbe13709cb",     5675535474154450433,     9949575000000000000),
    ("0x41bf39033c732f884a52ddf38f647ad63457ceec",     7275742623078676417,     9949575000000000000),
    ("0x5bbe6c46edeb35d558f5cd4bcd3875e710541309",     7411400935808275264,     8954617000000000000),
    ("0x19284cd63083583cf5c5e1f945fae112a39976c6",     2309443278589586836,     6015104000000000000),
    ("0x45f1cf510e78e029a0ddf697dd37ebc5f7921753",      479253106733869000,     5822352000000000000),
    ("0x28bd1999b747850c4409f740a0471ede16080617",     2068479694982380552,     5605193000000000000),
    ("0xfc7c1d00b2ec6d3653e9de72590684456846c53d",       78019664206849115,     5292130000000000000),
    ("0x9bc27f929c72ece55a0dcb0a1d845ec90be95275",     2763342511665497937,     4974787000000000000),
    ("0xca0073964efe7f9422ceb16901018b1db0cc4785",     1831041601954281300,     4727914000000000000),
    ("0xd088bdc872076691abb10ef128703e089e463047",       18649123714695394,     2387898000000000000),
    ("0xf52ebe90c4653b348b4c282a0172026f9c91ae5d",            1706494082256,     1512926000000000000),
    ("0x8d804669c3e1dec71ba8d460caaed5bf9fa415e2",            1274755592980,      977966000000000000),
    ("0x2c1e54f815529467be8f3b78e46c14168852322a",       73510880298701401,      709606000000000000),
    ("0xba49a3d456de4e670a94e13b8b1e5315929c97ad",      399616582905577779,      489858000000000000),
    ("0x3a3af2ea20d59da1caae5408c48a313ae12eed90",      483873000000000000,      483873000000000000),
]


def _summarize_error(exc: Exception) -> str:
    text = str(exc)
    # Boa's trace lists the call stack inside a "===" banner; lines starting
    # with "[E]" are the failing frames (deepest = innermost revert). After
    # preloading downstream contracts, the deepest [E] line includes the
    # source location and any "<dev: ...>" / "<reason: ...>" annotation.
    deepest_error_line = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[E]"):
            deepest_error_line = s

    if deepest_error_line:
        return deepest_error_line[:240]

    # Fall back: any line carrying a known marker
    for line in text.splitlines():
        s = line.strip()
        for marker in ("<dev:", "<reason:", "revert:", "Reason:"):
            if marker in s:
                return s[:240]

    # Last resort: first non-banner line
    for line in text.splitlines():
        s = line.strip()
        if s and set(s) > {"=", "-", "_"}:
            return s[:240]
    return text[:240]


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    sb_delta = migration.get_contract("SwitchboardDelta")

    # Pre-register downstream contracts at their *current* on-chain addresses
    # (manifest may be stale). Without this, boa shows "Unknown contract" and
    # we lose the dev string.
    DEPT_FILES = {
        3: "contracts/core/Teller.vy",
        5: "contracts/core/MissionControl.vy",
        7: "contracts/registries/PriceDesk.vy",
        8: "contracts/registries/VaultBook.vy",
        9: "contracts/core/AuctionHouse.vy",
        13: "contracts/core/CreditEngine.vy",
        17: "contracts/core/Teller.vy",
        18: "contracts/core/Deleverage.vy",
    }
    for dept_id, file_path in DEPT_FILES.items():
        try:
            addr = hq.getAddr(dept_id)
            if int(addr, 16) == 0:
                continue
            boa.load_partial(file_path).at(addr)
            log.h3(f"loaded dept {dept_id} -> {file_path} @ {addr}")
        except Exception as e:
            log.h3(f"could not load dept {dept_id} ({file_path}): {e}")

    gov = hq.governance()
    try:
        boa.env.set_balance(gov, 10 * 10**18)
    except Exception:
        pass

    # Show what each register ID resolves to, so the bug stares back.
    addr_at_3 = hq.getAddr(3)
    addr_at_17 = hq.getAddr(17)
    addr_at_18 = hq.getAddr(18)
    ripe_token_addr = hq.ripeToken() if hasattr(hq, "ripeToken") else None

    log.h1("Registry sanity check")
    log.h2(f"RipeHq.getAddr(3)   = {addr_at_3}   (SwitchboardDelta calls this as 'Teller')")
    log.h2(f"RipeHq.getAddr(17)  = {addr_at_17}  (Addys.TELLER_ID = 17)")
    log.h2(f"RipeHq.getAddr(18)  = {addr_at_18}  (DELEVERAGE_ID = 18)")
    if ripe_token_addr is not None:
        log.h2(f"RipeHq.ripeToken()  = {ripe_token_addr}")
    if addr_at_3 != addr_at_17:
        log.error(
            "BUG: SwitchboardDelta.TELLER_ID = 3 resolves to a different "
            "address than Addys.TELLER_ID = 17. SwitchboardDelta is calling "
            "the wrong contract (likely the RIPE token at register id 3)."
        )

    log.h2(f"Governance:        {gov}")
    log.h2(f"SwitchboardDelta:  {sb_delta.address}")
    log.h2(f"Asset (undy USD):  {ASSET}")
    log.h2(f"Vault id:          {VAULT_ID}")
    log.h2(f"Entries:           {len(DELEVERAGE_LIST)}")

    successes = []
    failures = []
    first_error_dumped = False

    for user, target_repay, capped_target in DELEVERAGE_LIST:
        assets = [(VAULT_ID, ASSET, target_repay)]
        try:
            repaid = sb_delta.deleverageWithSpecificAssets(assets, user, sender=gov)
            successes.append((user, repaid))
            log.h3(f"OK   {user}  repaid={repaid}")
        except Exception as e:
            if not first_error_dumped:
                first_error_dumped = True
                log.h1("Full error from first failure (for parsing reference)")
                log.info(repr(e))
                log.info("---")
                log.info(str(e))
                log.h1("End first failure dump")
            reason = _summarize_error(e)
            failures.append((user, target_repay, reason))
            log.h3(f"FAIL {user}  target={target_repay}  -> {reason}")

    log.h1("Summary")
    log.h2(f"OK:   {len(successes)} / {len(DELEVERAGE_LIST)}")
    log.h2(f"Fail: {len(failures)}")

    if failures:
        log.h1("Failures grouped by reason")
        by_reason: dict[str, list[str]] = {}
        for user, _target, reason in failures:
            by_reason.setdefault(reason, []).append(user)
        for reason, users in by_reason.items():
            log.h2(f"[{len(users)}]  {reason}")
            for u in users:
                log.h3(f"   {u}")
