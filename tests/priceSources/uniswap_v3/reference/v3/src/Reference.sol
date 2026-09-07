// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;
import "../vendor/v3-core/contracts/libraries/TickMath.sol";
import "../vendor/v3-core/contracts/libraries/FullMath.sol";
import "../vendor/v3-periphery/contracts/libraries/OracleLibrary.sol";
import "../vendor/v3-core/contracts/UniswapV3Factory.sol";
contract Reference {
    function sqrt(int24 tick) external pure returns (uint160) { return TickMath.getSqrtRatioAtTick(tick); }
    function quote(int24 tick, uint128 amount, address base, address counter) external pure returns (uint256) { return OracleLibrary.getQuoteAtTick(tick, amount, base, counter); }
    function mulDiv(uint256 a, uint256 b, uint256 d) external pure returns (uint256) { return FullMath.mulDiv(a,b,d); }
    function consult(address pool, uint32 window) external view returns (int24,uint128) { return OracleLibrary.consult(pool,window); }
}
