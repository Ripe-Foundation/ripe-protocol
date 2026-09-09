def test_g7_record_deployed_psm_runtime(endaoment_psm):
    n = len(endaoment_psm.env.get_code(endaoment_psm.address))
    print(f"PSM_DEPLOYED_RUNTIME {n} HEADROOM {24576 - n}")
    assert n <= 24576
