// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.24;

import {IBurnMintERC20} from "./v0.8/shared/token/ERC20/IBurnMintERC20.sol";
import {BurnMintTokenPool} from "./v0.8/ccip/pools/BurnMintTokenPool.sol";

/// @notice Legacy configurable-capability pool retained for testnet migration history.
/// @dev This is not the source of the live Base or Robinhood mainnet pools. Live
/// production provenance is RipeCcipBurnMintTokenPools.sol, whose token-specific
/// capability answers are compiled in as pure functions.
/// @dev Identical to `BurnMintTokenPool 1.5.1` except it implements the two functions
/// RipeHq expects on any address that holds minting privileges:
///
///   - `RipeHq.initiateHqConfigChange()` / `confirmHqConfigChange()` staticcall these to
///     validate a config before granting mint rights ("two-factor auth on minting").
///   - `RipeHq.canMintGreen(addr)` / `canMintRipe(addr)` staticcall these on every mint,
///     so `GreenToken.mint()` / `RipeToken.mint()` revert unless the pool confirms it too.
///
/// Both are set at deployment and immutable after it - a pool declares which token it is
/// for, and RipeHq can only grant it what it declared. Deploy one pool per token.
contract RipeTokenPool is BurnMintTokenPool {
  bool internal immutable i_canMintGreen;
  bool internal immutable i_canMintRipe;

  constructor(
    IBurnMintERC20 token,
    uint8 localTokenDecimals,
    address[] memory allowlist,
    address rmnProxy,
    address router,
    bool canMintGreen_,
    bool canMintRipe_
  ) BurnMintTokenPool(token, localTokenDecimals, allowlist, rmnProxy, router) {
    i_canMintGreen = canMintGreen_;
    i_canMintRipe = canMintRipe_;
  }

  /// @notice Whether this pool is allowed to mint GREEN, as far as this pool is concerned.
  /// @dev Read by RipeHq, both when granting mint rights and on every mint.
  function canMintGreen() external view returns (bool) {
    return i_canMintGreen;
  }

  /// @notice Whether this pool is allowed to mint RIPE, as far as this pool is concerned.
  /// @dev Read by RipeHq, both when granting mint rights and on every mint.
  function canMintRipe() external view returns (bool) {
    return i_canMintRipe;
  }
}
