pragma solidity ^0.5.8;


contract MerkleDrop {

    bytes32 public root;

    constructor(bytes32 _root) public {
        root = _root;
    }

    function withdraw(address recipient, uint value, bytes32[] memory proof) public {
        require(checkEntitlement(recipient, value, proof), "The proof could not be verified.");
    }

    function checkEntitlement(address recipient, uint value, bytes32[] memory proof) public view returns (bool) {
        // We need to pack pack the 20 bytes address to the 32 bytes value
        // to match with the proof made with the python merkle-drop package
        bytes32 leaf = keccak256(abi.encodePacked(recipient, value));
        return verifyProof(leaf, proof);
    }

    function verifyProof(bytes32 leaf, bytes32[] memory proof) view internal returns (bool) {
        bytes32 currentHash = leaf;

        for (uint i = 0; i <= proof.length - 1; i += 1) {
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
}
