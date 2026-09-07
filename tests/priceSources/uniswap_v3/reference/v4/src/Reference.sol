// SPDX-License-Identifier: MIT
pragma solidity =0.8.26;
import "../vendor/v4-core/src/libraries/TickMath.sol";
import "../vendor/v4-core/src/libraries/FullMath.sol";
contract Reference {
    function sqrt(int24 tick) external pure returns (uint160) { return TickMath.getSqrtPriceAtTick(tick); }
    function mulDiv(uint256 a, uint256 b, uint256 d) external pure returns (uint256) { return FullMath.mulDiv(a,b,d); }
    // Quote composition follows the RIPE arithmetic specification.
    function quote(int24 tick, uint128 amount, address base, address counter) external pure returns (uint256) {
        uint160 s = TickMath.getSqrtPriceAtTick(tick);
        if (s <= type(uint128).max) {
            uint256 r = uint256(s)*s;
            return base < counter ? FullMath.mulDiv(r, amount, 1<<192) : FullMath.mulDiv(1<<192, amount, r);
        }
        uint256 r = FullMath.mulDiv(s,s,1<<64);
        return base < counter ? FullMath.mulDiv(r,amount,1<<128) : FullMath.mulDiv(1<<128,amount,r);
    }
}
