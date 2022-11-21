// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract XmasLootBox is ERC721URIStorage, Ownable {

    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    constructor() ERC721("XmasLootBox", "XLX") {}

    function mintNFT(address recipient, string memory tokenURI)
        public onlyOwner
    {

        _tokenIds.increment();

        uint256 newItemId = _tokenIds.current();
        _mint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);

    }

    function mint4NFTs(address recipient, string[4] memory tokenURIs)
        public onlyOwner
    {
        for(uint i=0; i<4; i++){
            mintNFT(recipient, tokenURIs[i]);
        }
    }

    function totalSupply() external view returns (uint256){
        return _tokenIds.current();
    }
}
