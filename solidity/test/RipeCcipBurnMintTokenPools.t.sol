// SPDX-License-Identifier: LicenseRef-Ripe-Protocol-License
pragma solidity ^0.8.24;

import {GreenCcipBurnMintTokenPool, RipeCcipBurnMintTokenPool} from "../src/RipeCcipBurnMintTokenPools.sol";
import {IBurnMintERC20} from "../src/v0.8/shared/token/ERC20/IBurnMintERC20.sol";

contract MockBurnMintERC20 is IBurnMintERC20 {
    uint8 public constant decimals = 18;

    function totalSupply() external pure override returns (uint256) {
        return 0;
    }

    function balanceOf(address) external pure override returns (uint256) {
        return 0;
    }

    function transfer(address, uint256) external pure override returns (bool) {
        return true;
    }

    function allowance(address, address) external pure override returns (uint256) {
        return 0;
    }

    function approve(address, uint256) external pure override returns (bool) {
        return true;
    }

    function transferFrom(address, address, uint256) external pure override returns (bool) {
        return true;
    }

    function mint(address, uint256) external pure override {}
    function burn(uint256) external pure override {}
    function burn(address, uint256) external pure override {}
    function burnFrom(address, uint256) external pure override {}
}

interface IAdministeredPool {
    function setRateLimitAdmin(address admin) external;
    function getRateLimitAdmin() external view returns (address);
    function setRouter(address router) external;
    function getRouter() external view returns (address);
}

contract UntrustedPoolCaller {
    function trySetRateLimitAdmin(address pool, address admin) external returns (bool) {
        (bool ok,) = pool.call(abi.encodeCall(IAdministeredPool.setRateLimitAdmin, (admin)));
        return ok;
    }

    function trySetRouter(address pool, address router) external returns (bool) {
        (bool ok,) = pool.call(abi.encodeCall(IAdministeredPool.setRouter, (router)));
        return ok;
    }
}

abstract contract PoolTestBase {
    address internal constant RMN_PROXY = address(0x1111);
    address internal constant ROUTER = address(0x2222);

    MockBurnMintERC20 internal token;

    constructor() {
        token = new MockBurnMintERC20();
    }

    function _emptyAllowlist() internal pure returns (address[] memory) {
        return new address[](0);
    }

    function _isPinnedVersion(string memory value) internal pure returns (bool) {
        return keccak256(bytes(value)) == keccak256(bytes("BurnMintTokenPool 1.5.1"));
    }

    function _assertInheritedOwnerControls(address pool) internal {
        UntrustedPoolCaller caller = new UntrustedPoolCaller();
        address newAdmin = address(0x3333);
        address newRouter = address(0x4444);
        require(!caller.trySetRateLimitAdmin(pool, newAdmin), "non-owner changed rate admin");
        require(!caller.trySetRouter(pool, newRouter), "non-owner changed router");

        IAdministeredPool(pool).setRateLimitAdmin(newAdmin);
        IAdministeredPool(pool).setRouter(newRouter);
        require(IAdministeredPool(pool).getRateLimitAdmin() == newAdmin, "owner rate admin");
        require(IAdministeredPool(pool).getRouter() == newRouter, "owner router");
    }
}

contract GreenCcipBurnMintTokenPoolTest is PoolTestBase {
    GreenCcipBurnMintTokenPool internal greenPool;

    constructor() {
        greenPool = new GreenCcipBurnMintTokenPool(token, 18, _emptyAllowlist(), RMN_PROXY, ROUTER);
    }

    function testGreenCapabilityIsCompiledIn() public view {
        require(greenPool.canMintGreen(), "GREEN pool must declare GREEN");
        require(!greenPool.canMintRipe(), "GREEN pool must reject RIPE");
    }

    function testGreenPoolRetainsPinnedVersionAndConstructorBindings() public view {
        require(_isPinnedVersion(greenPool.typeAndVersion()), "GREEN source version");
        require(address(greenPool.getToken()) == address(token), "GREEN token");
        require(greenPool.getRmnProxy() == RMN_PROXY, "GREEN RMN");
        require(greenPool.getRouter() == ROUTER, "GREEN router");
        require(greenPool.owner() == address(this), "GREEN owner");
        require(greenPool.getRateLimitAdmin() == address(0), "GREEN rate admin");
    }

    function testGreenPoolRetainsInheritedOwnerControls() public {
        _assertInheritedOwnerControls(address(greenPool));
    }

    function testGreenConstructorTokenBindingIsExplicit() public {
        MockBurnMintERC20 otherToken = new MockBurnMintERC20();
        GreenCcipBurnMintTokenPool otherPool =
            new GreenCcipBurnMintTokenPool(otherToken, 18, _emptyAllowlist(), RMN_PROXY, ROUTER);
        require(address(otherPool.getToken()) == address(otherToken), "explicit GREEN token");
    }
}

contract RipeCcipBurnMintTokenPoolTest is PoolTestBase {
    RipeCcipBurnMintTokenPool internal ripePool;

    constructor() {
        ripePool = new RipeCcipBurnMintTokenPool(token, 18, _emptyAllowlist(), RMN_PROXY, ROUTER);
    }

    function testRipeCapabilityIsCompiledIn() public view {
        require(!ripePool.canMintGreen(), "RIPE pool must reject GREEN");
        require(ripePool.canMintRipe(), "RIPE pool must declare RIPE");
    }

    function testRipePoolRetainsPinnedVersionAndConstructorBindings() public view {
        require(_isPinnedVersion(ripePool.typeAndVersion()), "RIPE source version");
        require(address(ripePool.getToken()) == address(token), "RIPE token");
        require(ripePool.getRmnProxy() == RMN_PROXY, "RIPE RMN");
        require(ripePool.getRouter() == ROUTER, "RIPE router");
        require(ripePool.owner() == address(this), "RIPE owner");
        require(ripePool.getRateLimitAdmin() == address(0), "RIPE rate admin");
    }

    function testRipePoolRetainsInheritedOwnerControls() public {
        _assertInheritedOwnerControls(address(ripePool));
    }
}
