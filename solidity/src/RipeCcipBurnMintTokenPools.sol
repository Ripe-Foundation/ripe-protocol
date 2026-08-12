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
// One contract per capability, with the answers compiled in as `pure` rather
// than taken as constructor flags. This prevents GREEN/RIPE capability flags
// from being passed in the wrong order. The inherited constructor still accepts
// an arbitrary token, so deployment tooling must bind and revalidate getToken().
//
// This is the repository candidate/reference implementation for token-specific
// pools that inherit the vendored `BurnMintTokenPool 1.5.1`. Onchain topology,
// capability, type/version, and runtime-hash evidence does not by itself prove
// that the live Base or Robinhood pools were created from this source. The exact
// live source set, compiler version/settings, constructor arguments, and
// creation-artifact identity remain unresolved. The 1.6.1 example under docs/
// is retained only as superseded design research. foundry.toml pins settings
// for compiling this repository candidate; it is not live-creation provenance.

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
