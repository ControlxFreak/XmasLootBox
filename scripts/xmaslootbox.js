const { Web3Storage, getFilesFromPath } = require("web3.storage");
const { argv } = require('node:process');
const fs = require('fs')
require('dotenv').config()

const addresses = {
  "aoth": "0xbCC9CB013524B61bA0272ccF1Eaae89AA335e1BE"
}

async function main(){
    // Extract the information from the input arguments
    // Args: 0: node 1: <this file> 2: username 3: nft_dir 4: data_dir
    const username = process.argv[2]
    const nft_dir = process.argv[3]
    const data_dir = process.argv[4]

    // Construct with token and endpoint
    // const w3sclient = new Web3Storage({ token: process.env.W3STORAGE_API_TOKEN });

    // // Get all of the NFT files and put them on IPFS
    // const nft_files = await getFilesFromPath(nft_dir);
    // const nft_root = await w3sclient.put(nft_files);
    // console.log("Uploaded ", file.name, " to IPFS at CID: ", nft_root);
    nft_root = "bafybeiaux2zegbgkz6awo4echcmipuzvtnzsveyi27hxxvzdbpmm5yrhqe";

    // Update the data files with the corresponding CID
    const data_files = await getFilesFromPath(data_dir);
    for (const data_file of data_files) {
      // Read this file
      let rawdata = fs.readFileSync(data_file.name);
      let metadata = JSON.parse(rawdata);
      // Update the image field with the corresponding CID
      metadata.image = nft_root;
      // Rewrite the json file
      metadata = JSON.stringify(metadata);
      fs.writeFile(data_file, metadata, (err) => {
        // Error checking
        if (err) throw err;
        console.log("Overwrote CID field in ", data_file.name);
      });
    }

    // Get the user's address from their username
    const useraddr = addresses[username]
    console.log("User Address: ", useraddr)

  }

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
});