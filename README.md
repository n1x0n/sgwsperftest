# n1x0n/sgwsperftest
Docker image that I use for performance tests against NetApp StorageGRID Webscale.

# Usage
You might need to modify the code to suit your environment, but I think I managed to move most of those specifics to config.ini. (Open an Issue if I missed something.)

Here is a basic rundown of how I use the image.

## 1. Download self-signed certificate from any storage node using update_cert.sh.
```
 ./update_cert.sh node-01 18082 server.pem
```
This will store the certificate from node-01:18082 to server.pem.
