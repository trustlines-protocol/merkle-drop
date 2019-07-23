pragma solidity ^0.5.8;

import "./DroppedToken.sol";


contract MerkleDrop {

    bytes32 public root;
    DroppedToken public droppedToken;
    uint public decayStartTime;
    uint public decayDurationInSeconds;

    uint public initialBalance;
    uint public remainingValue;  // The total not decayed not withdrawn entitlements
    uint public spentTokens;  // The total tokens spent by the contract, burnt or withdrawn

    mapping (address => bool) public withdrawn;

    event Withdraw(address recipient, uint value);
    event Burn(uint value);

    constructor(DroppedToken _droppedToken, uint _initialBalance, bytes32 _root, uint _decayStartTime, uint _decayDurationInSeconds) public {
        droppedToken = _droppedToken;
        initialBalance = _initialBalance;
        remainingValue = _initialBalance;
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

        burnUnusableTokens();

        uint valueToSend = decayedEntitlementAtTime(value, now, false);
        assert(valueToSend <= value);
        require(droppedToken.balanceOf(address(this)) >= valueToSend, "The MerkleDrop does not have tokens to drop yet / anymore.");
        require(valueToSend != 0, "The decayed entitled value is now null.");

        withdrawn[recipient] = true;
        remainingValue -= value;
        spentTokens += valueToSend;

        droppedToken.transfer(recipient, valueToSend);
        emit Withdraw(recipient, value);
    }

    function verifyEntitled(address recipient, uint value, bytes32[] memory proof) public view returns (bool) {
        // We need to pack pack the 20 bytes address to the 32 bytes value
        // to match with the proof made with the python merkle-drop package
        bytes32 leaf = keccak256(abi.encodePacked(recipient, value));
        return verifyProof(leaf, proof);
    }

    function decayedEntitlementAtTime(uint value, uint time, bool roundUp) public view returns (uint) {
        if (time <= decayStartTime) {
            return value;
        } else if (time >= decayStartTime + decayDurationInSeconds) {
            return 0;
        } else {
            uint timeDecayed = time - decayStartTime;
            uint valueDecay = decay(value, timeDecayed, decayDurationInSeconds, !roundUp);
            assert(valueDecay <= value);
            return value - valueDecay;
        }
    }

    function burnUnusableTokens() public {
        if (now <= decayStartTime) {
            return;
        }

        // The amount of tokens that should be held within the contract after burning
        uint targetBalance = decayedEntitlementAtTime(remainingValue, now, true);

        // toBurn = (initial balance - target balance) - what we already removed from initial balance
        uint currentBalance = initialBalance - spentTokens;
        assert(targetBalance <= currentBalance);
        uint toBurn = currentBalance - targetBalance;

        spentTokens += toBurn;
        burn(toBurn);
    }

    function deleteContract() public {
        require(now >= decayStartTime + decayDurationInSeconds, "The storage cannot be deleted before the end of the merkle drop.");
        burnUnusableTokens();

        selfdestruct(address(0));
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
        if (value == 0) {
            return;
        }
        emit Burn(value);
        droppedToken.burn(value);
    }

    function decay(uint value, uint timeToDecay, uint totalDecayTime, bool roundUp) internal pure returns (uint) {
        uint decay = value*timeToDecay/totalDecayTime;
        if (decay * totalDecayTime != value * timeToDecay && roundUp) {
            decay = decay + 1;
        }
        return decay >= value ? value : decay;
    }
}
