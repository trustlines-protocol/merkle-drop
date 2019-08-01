pragma solidity ^0.5.8;

import "./SafeMath.sol";
import "./MerkleDrop.sol";


// This token is a copy of the TrustlinesNetworkToken as of commit 0651fb21bc35380a551988a8dc9fedd763abb253.
// The burn and transfer functions have been modified for test purpose.
// It is used for testing the MerkleDrop contract.
// The MerkleDrop contract is able to drop any ERC20 token however.

// This contract should not be deployed

contract DroppedToken is ERC20Interface {

    using SafeMath for uint256;

    uint constant MAX_UINT = 2**256 - 1;
    string private _name;
    string private _symbol;
    uint8 private _decimals;
    uint256 private _totalSupply;
    bool private burnLoopFlag;

    MerkleDrop public merkleDrop;

    mapping (address => uint256) private _balances;
    mapping (address => mapping (address => uint256)) private _allowances;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor (string memory name, string memory symbol, uint8 decimals, address preMintAddress, uint256 preMintAmount) public {
        _name = name;
        _symbol = symbol;
        _decimals = decimals;

        _mint(preMintAddress, preMintAmount);
    }

    function storeAddressOfMerkleDrop(address _merkleDrop) public {
        merkleDrop = MerkleDrop(_merkleDrop);
    }

    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    function allowance(address owner, address spender) public view returns (uint256) {
        return _allowances[owner][spender];
    }

    function name() public view returns (string memory) {
        return _name;
    }

    function symbol() public view returns (string memory) {
        return _symbol;
    }

    function decimals() public view returns (uint8) {
        return _decimals;
    }

    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    function transfer(address recipient, uint256 amount) public returns (bool) {
        // We call merkleDrop.burnUnusableTokens() here as a test to see if it will burn too many tokens if we call it before updating the balances.
        if (address(merkleDrop) != address(0)) {
            merkleDrop.burnUnusableTokens();
        }
        _transfer(msg.sender, recipient, amount);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        require(value == 0 || _allowances[msg.sender][spender] == 0, "ERC20: approve only to or from 0 value");
        _approve(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount) public returns (bool) {
        _transfer(sender, recipient, amount);

        uint allowance = _allowances[sender][msg.sender];
        uint updatedAllowance = allowance.sub(amount);
        if (allowance < MAX_UINT) {
            _approve(sender, msg.sender, updatedAllowance);
        }
        return true;
    }

    function burn(uint256 amount) public {
        // We call merkleDrop.burnUnusableTokens() here as a test to see if it will burn too many tokens if we re-enter it.
        // We use the burnLoopFlag to prevent an infinite loop of calls, knowing MerkleDrop.sol calls the burn function again.
        if (! burnLoopFlag && address(merkleDrop) != address(0)) {
            burnLoopFlag = true;
            merkleDrop.burnUnusableTokens();
        }
        _burn(msg.sender, amount);
        burnLoopFlag = false;
    }

    function _mint(address account, uint256 amount) internal {
        require(account != address(0), "ERC20: mint to the zero address");

        _totalSupply = _totalSupply.add(amount);
        _balances[account] = _balances[account].add(amount);
        emit Transfer(address(0), account, amount);
    }

    function _transfer(address sender, address recipient, uint256 amount) internal {
        require(sender != address(0), "ERC20: transfer from the zero address");
        require(recipient != address(0), "ERC20: transfer to the zero address");

        _balances[sender] = _balances[sender].sub(amount);
        _balances[recipient] = _balances[recipient].add(amount);
        emit Transfer(sender, recipient, amount);
    }

    function _approve(address owner, address spender, uint256 value) internal {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = value;
        emit Approval(owner, spender, value);
    }

    function _burn(address account, uint256 value) internal {
        require(account != address(0), "ERC20: burn from the zero address");

        _totalSupply = _totalSupply.sub(value);
        _balances[account] = _balances[account].sub(value);
        emit Transfer(account, address(0), value);
    }
}

/*
The MIT License (MIT)

Copyright (c) 2016-2019 zOS Global Limited

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
*/
