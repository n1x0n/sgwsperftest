# n1x0n/sgwsperftest
Docker image that I use for performance tests against NetApp StorageGRID Webscale.

# Usage
1. Download self-signed certificate from any storage node using update_cert.sh.
 ./update_cert.sh node-01 18082 server.pem
This will store the certificate from node-01:18082 to server.pem.
