// SPDX-License-Identifier: LicenseRef-Ripe-Protocol-License
pragma solidity ^0.8.24;

import {BurnMintTokenPool} from "@chainlink/contracts-ccip/contracts/pools/BurnMintTokenPool.sol";
import {IBurnMintERC20} from "@chainlink/contracts/src/v0.8/shared/token/ERC20/IBurnMintERC20.sol";

/// @notice Chainlink CCIP v1.6.1 burn/mint pool for GREEN.
/// @dev The inherited pool contains all CCIP, ownership, RMN, allowlist,
/// remote-chain, and rate-limit behavior. These two views are the only
/// Ripe-specific runtime behavior added by this contract.
contract GreenCcipBurnMintTokenPool is BurnMintTokenPool {
    constructor(
        IBurnMintERC20 token,
        uint8 localTokenDecimals,
        address[] memory allowlist,
        address rmnProxy,
        address router
    ) BurnMintTokenPool(token, localTokenDecimals, allowlist, rmnProxy, router) {}

    function canMintGreen() external pure returns (bool) {
        return true;
    }

    function canMintRipe() external pure returns (bool) {
        return false;
    }
}

/// @notice Chainlink CCIP v1.6.1 burn/mint pool for RIPE.
/// @dev The inherited pool contains all CCIP, ownership, RMN, allowlist,
/// remote-chain, and rate-limit behavior. These two views are the only
/// Ripe-specific runtime behavior added by this contract.
contract RipeCcipBurnMintTokenPool is BurnMintTokenPool {
    constructor(
        IBurnMintERC20 token,
        uint8 localTokenDecimals,
        address[] memory allowlist,
        address rmnProxy,
        address router
    ) BurnMintTokenPool(token, localTokenDecimals, allowlist, rmnProxy, router) {}

    function canMintGreen() external pure returns (bool) {
        return false;
    }

    function canMintRipe() external pure returns (bool) {
        return true;
    }
}
