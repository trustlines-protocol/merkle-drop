pragma solidity ^0.5.8;

import "./DroppedToken.sol";


contract MerkleDrop {

    bytes32 public root;
    DroppedToken public droppedToken;
    uint public decayStartTime;
    uint public decayDurationInSeconds;
    uint public lastBurnTime;

    uint public initialEntitlement = 15000000;  // just for testing, need to be set in the constructor
    uint public withdrawnValue;
    uint public burntTokens;

    mapping (address => bool) withdrawn;

    event Withdraw(address recipient, uint value);
    event Burn(uint value);

    constructor(DroppedToken _droppedToken, bytes32 _root, uint _decayStartTime, uint _decayDurationInSeconds) public {
        droppedToken = _droppedToken;
        root = _root;
        decayStartTime = _decayStartTime;
        decayDurationInSeconds = _decayDurationInSeconds;
    }

    function withdraw(uint value, bytes32[] memory proof) public {
        withdrawFor(msg.sender, value, proof);
    }

    function withdrawFor(address recipient, uint value, bytes32[] memory proof) public {
        require(verifyEntitled(recipient, value, proof), "The proof could not be verified.");
        require(! withdrawn[recipient], "The recipient has already withdrawn its entitled token.");

        uint valueToSend = decayedEntitlementAtTime(value, now);
        assert(valueToSend <= value);
        require(droppedToken.balanceOf(address(this)) >= valueToSend, "The MerkleDrop does not have tokens to drop yet / anymore.");
        require(valueToSend != 0, "The decayed entitled value is now null.");

        withdrawn[recipient] = true;
        withdrawnValue += value;

        // we burn the value not sent that has not been burnt via burnUnusableTokens yet.
        uint valueToBurn;
        if (lastBurnTime == 0) {
            valueToBurn = value - valueToSend;
        } else {
            valueToBurn = value * (now - lastBurnTime)/decayDurationInSeconds;
        }
        // burn(valueToBurn);

        droppedToken.transfer(recipient, valueToSend);
        emit Withdraw(recipient, value);
    }

    function verifyEntitled(address recipient, uint value, bytes32[] memory proof) public view returns (bool) {
        // We need to pack pack the 20 bytes address to the 32 bytes value
        // to match with the proof made with the python merkle-drop package
        bytes32 leaf = keccak256(abi.encodePacked(recipient, value));
        return verifyProof(leaf, proof);
    }

    function decayedEntitlementAtTime(uint value, uint time) public view returns (uint) {
        if (time <= decayStartTime) {
            return value;
        } else if (time >= decayStartTime + decayDurationInSeconds) {
            return 0;
        } else {
            uint timeDecayed = time - decayStartTime;
            uint valueDecay = decay(value, timeDecayed, decayDurationInSeconds);
            assert(valueDecay <= value);
            return value - valueDecay;
        }
    }

    function burnUnusableTokens() public {
        require(now >= decayStartTime, "The decay start time has not been reached yet, there is no token to burn.");
        uint decayEndTime = decayStartTime + decayDurationInSeconds;
        if (now >= decayEndTime) {
            lastBurnTime = now;
            burn(droppedToken.balanceOf(address(this)));
            return;
        }

        uint remainingValue = initialEntitlement - withdrawnValue;
        uint decayedRemainingValue = remainingValue - decay(remainingValue, now - decayStartTime, decayDurationInSeconds);
        // need to check whether rounding errors burns too much or not enough

        uint currentBalance = droppedToken.balanceOf(address(this));

        uint toBurn = currentBalance - decayedRemainingValue;

        burntTokens += toBurn;

        burn(toBurn);
        return;
    }

    function verifyProof(bytes32 leaf, bytes32[] memory proof) internal view returns (bool) {
        bytes32 currentHash = leaf;

        for (uint i = 0; i < proof.length; i += 1) {
            currentHash = parentHash(currentHash, proof[i]);
        }

        return currentHash == root;
    }

    function parentHash(bytes32 a, bytes32 b) internal pure returns (bytes32) {
        if (a < b) {
            return keccak256(abi.encode(a, b));
        } else {
            return keccak256(abi.encode(b, a));
        }
    }

    function burn(uint value) internal {
        emit Burn(value);
        droppedToken.burn(value);
    }

    function decay(uint value, uint timeToDecay, uint totalDecayTime) internal pure returns (uint) {
        return value*timeToDecay/totalDecayTime;
    }
}
