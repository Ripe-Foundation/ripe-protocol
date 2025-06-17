# @version 0.4.1

struct TemporalNumericValue:
    timestampNs: uint64
    quantizedValue: uint256

struct TemporalNumericValueInput:
    temporalNumericValue: TemporalNumericValue
    id: bytes32
    publisherMerkleRoot: bytes32
    valueComputeAlgHash: bytes32
    r: bytes32
    s: bytes32
    v: uint8


priceFeeds: public(HashMap[bytes32, TemporalNumericValue])


@deploy
def __init__():
    # initialize "usdc" feed
    usdcId: bytes32 = 0x7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c
    usdcFeed: TemporalNumericValue = TemporalNumericValue(
        timestampNs=convert(block.timestamp * 1_000_000_000, uint64),
        quantizedValue=999879984000000000
    )
    self.priceFeeds[usdcId] = usdcFeed


@view
@external
def getTemporalNumericValueUnsafeV1(_priceFeedId: bytes32) -> TemporalNumericValue:
    return  self.priceFeeds[_priceFeedId]


@view
@external
def getUpdateFeeV1(_payLoad: Bytes[2048]) -> uint256:
    return len(_payLoad)


@payable
@external
def updateTemporalNumericValuesV1(_payLoad: Bytes[2048]):
    updateFee: uint256 = len(_payLoad)
    assert msg.value >= updateFee, "not enough eth"

    inputData: TemporalNumericValueInput = abi_decode(_payLoad, TemporalNumericValueInput)
    self.priceFeeds[inputData.id] = inputData.temporalNumericValue


@pure
@external
def createPriceFeedUpdateData(
    _id: bytes32,
    _price: uint256,
    _publishTime: uint256
) -> Bytes[2048]:
    inputData: TemporalNumericValueInput = TemporalNumericValueInput(
        temporalNumericValue=TemporalNumericValue(
            timestampNs=convert(_publishTime * 1_000_000_000, uint64),
            quantizedValue=_price,
        ),
        id=_id,
        publisherMerkleRoot=empty(bytes32),
        valueComputeAlgHash=empty(bytes32),
        r=empty(bytes32),
        s=empty(bytes32),
        v=0,
    )
    return abi_encode(inputData)



