#!/usr/bin/node
const { Web3Storage, getFilesFromPath } = require("web3.storage");
const ethers = require("ethers");
const path = require('path');
const fs = require('fs');
require('dotenv').config()

// ----------------------------------------------------------------- //
// Configuration
// ----------------------------------------------------------------- //
// Extract the information from the input arguments
const username = process.argv[2].toLowerCase()
const nft_dir = process.argv[3]
const data_dir = process.argv[4]

// Construct the web3 storage IPFS client
const w3sclient = new Web3Storage({ token: process.env.W3STORAGE_API_TOKEN });

// Configure the address and private key
const owner_address = process.env.OWNER_ADDRESS
const private_key = process.env.OWNER_PRIVATE_KEY

const addresses = {
  "aoth": owner_address
}

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
  const nft_base_uri = `ipfs:\/\/${nft_root}/`
  console.log("Uploaded NFT Images to: ", nft_base_uri)

  // =============================================================== //
  // Update each data file with the corresponding CID
  // =============================================================== //
  for (const data_file of data_files) {
    // Get the basename of this file (which should be the tokenID)
    var tokenID = path.basename(data_file.name, '.json');

    // Read this file
    var data_path = path.join(data_dir, tokenID.concat(".json"))
    var metadata = JSON.parse(fs.readFileSync(data_path))

    // Update the image field with the NFT image's corresponding CID
    var nft_uri = new URL(tokenID.concat(".gif"), nft_base_uri).href
    console.log("Updated Metadata URI: ", nft_uri)
    metadata.image = nft_uri
    console.log(metadata)

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
  const data_base_uri = `ipfs:\/\/${data_root}/`
  console.log("Uploaded Metadata to: ", data_base_uri)

  // =============================================================== //
  // Mint the NFT
  // =============================================================== //
  // Get the user's address from their username
  const user_address = addresses[username]
  const prev_balance = await contract.balanceOf(user_address)
  console.log("Minting NFTs to User Address: ", user_address)
  console.log("User originally has an NFT Balance of: ", prev_balance)

  for (const data_file of data_files) {
    // Get the basename of this file (which should be the tokenID)
    var tokenID = path.basename(data_file.name, '.json');

    // Call the mintNFT function in the smart contract
    var data_uri = new URL(tokenID.concat(".json"), data_base_uri).href
    console.log("Minting with URI: ", data_uri)
    var tx = await connected_contract.mintNFT(
      user_address,
      data_uri
    )
    await tx.wait()

    console.log("Minted Token ID: ", tokenID, " to ", username, "!")
  }

  // Show that your balance increased
  const post_balance = await contract.balanceOf(user_address)
  console.log("User now has an NFT Balance of: ", post_balance)

  // Report the amount of ether remaining in the owner
  const remaining_eth = await provider.getBalance(owner_address)
  console.log("Owner has: ", ethers.utils.formatEther(remaining_eth), " ETH remaining")

}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
});