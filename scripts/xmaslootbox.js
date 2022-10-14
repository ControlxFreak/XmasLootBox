#!/usr/bin/node
const { Web3Storage, getFilesFromPath } = require("web3.storage");
const ethers = require("ethers");
const argv = require('node:process');
const path = require('path');
const fs = require('fs')
require('dotenv').config()

// ----------------------------------------------------------------- //
// Configuration
// ----------------------------------------------------------------- //
// Extract the information from the input arguments
const username = process.argv[2]
const nft_dir = process.argv[3]
const data_dir = process.argv[4]

// Construct the web3 storage IPFS client
const w3sclient = new Web3Storage({ token: process.env.W3STORAGE_API_TOKEN });

// Construct the address mappings
const addresses = {
  "aoth": "0x3fAb8CC827b4C41Dc9e6C07d522fD2f48A431f23"
}

// Configure the owner's address and private key
const owner_address = process.env.OWNER_ADDRESS
const private_key = process.env.OWNER_PRIVATE_KEY

// Configure the Ethereum Network provider
const provider = new ethers.providers.AlchemyProvider(
    "goerli",
    process.env.ALCHEMY_API_TOKEN
)

// Configure the wallet
const wallet = new ethers.Wallet(private_key, provider)

// Configure the smart contract and connect our wallet to this contract
ERC721_ABI = [
    "function balanceOf(address) view returns (uint256)",
    "function mintNFT(address, string) returns (uint256)"
]
const contract_address = process.env.CONTRACT_ADDRESS
const contract = new ethers.Contract(contract_address, ERC721_ABI, provider)
const connected_contract = contract.connect(wallet)

// ----------------------------------------------------------------- //
// Script
// ----------------------------------------------------------------- //
async function main(){
  // =============================================================== //
  // Get the NFT and Data File Paths
  // =============================================================== //
  const nft_files = await getFilesFromPath(nft_dir);
  const data_files = await getFilesFromPath(data_dir);

  // =============================================================== //
  // Put the NFT images on IPFS
  // =============================================================== //
  const nft_root = await w3sclient.put(nft_files, { wrapWithDirectory: false });
  const nft_base_uri = `https://${nft_root}.ipfs.w3s.link/`
  console.log("Uploaded NFT Images to: ", nft_base_uri)

  // =============================================================== //
  // Update each data file with the corresponding CID
  // =============================================================== //
  for (const data_file of data_files) {
    // Get the basename of this file (which should be the tokenID)
    let tokenID = path.basename(data_file.name, '.json');

    // Read this file
    let data_path = path.join(data_dir, tokenID.concat(".json"))
    let metadata = JSON.parse(fs.readFileSync(data_path));

    // Update the image field with the NFT image's corresponding CID
    metadata.image = path.join(nft_base_uri, tokenID.concat(".gif"));

    // Overwrite the json file
    fs.writeFileSync(data_path, JSON.stringify(metadata), (err) => {
      // Error checking
      if (err) throw err;
    });

    console.log(`Updated NFT ${tokenID}'s metadata`)
  }

  // =============================================================== //
  // Push the data files to IPFS
  // =============================================================== //
  const data_root = await w3sclient.put(data_files, { wrapWithDirectory: false });
  const data_base_uri = `https://${data_root}.ipfs.w3s.link/`
  console.log("Uploaded Metadata to: ", data_base_uri)

  // =============================================================== //
  // Mint the NFT
  // =============================================================== //
  // Get the user's address from their username
  const user_address = addresses[username]
  const prev_balance = await contract.balanceOf(user_address)
  console.log("Minting NFTs to User Address: ", user_address)
  console.log("Previous Balance: ", prev_balance)

  var txarray = [];
  for (const data_file of data_files) {
    // Get the basename of this file (which should be the tokenID)
    let tokenID = path.basename(data_file.name, '.json');

    // Call the mintNFT function in the smart contract
    let tx = await connected_contract.mintNFT(
      user_address,
      path.join(data_base_uri, tokenID.concat(".json"))
    )
    txarray.push(tx)
    
    console.log("Minted Token ID: ", tokenID, " to ", username, "!")
  }

  // Wait for the transactions to be official before returning
  for(const tx of txarray) {
    await tx.wait()
  }

}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
});