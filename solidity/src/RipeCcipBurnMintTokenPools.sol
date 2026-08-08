// SPDX-License-Identifier: LicenseRef-Ripe-Protocol-License
pragma solidity ^0.8.24;

import {IBurnMintERC20} from "./v0.8/shared/token/ERC20/IBurnMintERC20.sol";
import {BurnMintTokenPool} from "./v0.8/ccip/pools/BurnMintTokenPool.sol";

// Chainlink CCIP burn/mint pools for the Ripe Protocol tokens.
//
// The inherited pool contains all CCIP, ownership, RMN, allowlist,
// remote-chain and rate-limit behavior. The two views below are the only
// Ripe-specific runtime behavior these contracts add, and they exist because
// RipeHq staticcalls them:
//
//   - RipeHq.initiateHqConfigChange() / confirmHqConfigChange() read them
//     before granting mint rights ("two-factor auth on minting").
//   - RipeHq.canMintGreen(addr) / canMintRipe(addr) read them on every mint,
//     so GreenToken.mint() / RipeToken.mint() revert unless the pool agrees.
//
// One contract per token, with the answers compiled in as `pure` rather than
// taken as constructor arguments. A pool cannot then be deployed claiming to
// be for a token it is not: the capability is a property of the bytecode, so
// it is visible in the verified source and cannot be got wrong by passing
// arguments in the wrong order.
//
// Ripe uses the vendored `BurnMintTokenPool 1.5.1` here rather than the 1.6.1
// package the reference in docs/ imports, because foundry.toml mirrors the
// settings Chainlink used for their verified 1.5.1 deployments -- so these
// build byte-identically to the upstream pool they extend. Both versions are
// in active use on Base and Robinhood mainnet.

/// @notice CCIP burn/mint pool for GREEN.
contract GreenCcipBurnMintTokenPool is BurnMintTokenPool {
    constructor(
        IBurnMintERC20 token,
        uint8 localTokenDecimals,
        address[] memory allowlist,
        address rmnProxy,
        address router
    ) BurnMintTokenPool(token, localTokenDecimals, allowlist, rmnProxy, router) {}

    /// @notice Whether this pool may mint GREEN, as far as this pool is concerned.
    function canMintGreen() external pure returns (bool) {
        return true;
    }

    /// @notice Whether this pool may mint RIPE, as far as this pool is concerned.
    function canMintRipe() external pure returns (bool) {
        return false;
    }
}

/// @notice CCIP burn/mint pool for RIPE.
contract RipeCcipBurnMintTokenPool is BurnMintTokenPool {
    constructor(
        IBurnMintERC20 token,
        uint8 localTokenDecimals,
        address[] memory allowlist,
        address rmnProxy,
        address router
    ) BurnMintTokenPool(token, localTokenDecimals, allowlist, rmnProxy, router) {}

    /// @notice Whether this pool may mint GREEN, as far as this pool is concerned.
    function canMintGreen() external pure returns (bool) {
        return false;
    }

    /// @notice Whether this pool may mint RIPE, as far as this pool is concerned.
    function canMintRipe() external pure returns (bool) {
        return true;
    }
}
