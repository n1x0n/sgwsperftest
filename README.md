# n1x0n/sgwsperftest
Docker image that I use for performance tests against NetApp StorageGRID Webscale.

# Usage
You might need to modify the code to suit your environment, but I think I managed to move most of those specifics to config.ini. (Open an Issue if I missed something.)

Here is a basic rundown of how I use the image. My recommendation is that you use a volume to store persistent configuration data, such as the server certificate and the config.ini file. In the lab where I run this we have NetApp storage and use the [NetApp Docker Volume Plugin](https://github.com/NetApp/netappdvp) which makes this so easy that it almosts feels like cheating. 

If you run Docker Swarm and the NetApp Docker Volume Plugin, any volumes you create will be available on all nodes in the swarm. If you store the configuration on that volume you can quickly spin up containers running the performance benchmark on several nodes in parallel which is how I use it.

```
# Run one container using the volume sgwsdata.
docker run -it --rm -v sgwsdata:/sgwsdata n1x0n/swgsperftest
```

## 1. Download self-signed certificate from any storage node using update_cert.sh.
When you install StorageGRID Webscale all the storage nodes and gateways will use a self-signed certificate for https traffic. You can replace this with a proper certificate, but in the lab I use we do not have that option. The `boto3` python module that we use is based on the `requests` module which allows you to specify a certificate file to verify the servers certificate against.

By downloading this certificate directly from one of the storage nodes we can store the certificate and verify the servers with that file.

```
 # Download the cert to server.pem
 ./update_cert.sh node-01 18082 server.pem
```

This will store the certificate from node-01:18082 to server.pem. Again, if you followed my advice and used a volume you should copy the certificate to somewhere on that volume.

## 2. Edit config.ini
Edit the config.ini file to match your environment. The file has comments describing all the settings. This is where you point out your StorageGRID environment and where you set how many concurrent threads you want to use.

Any changes to /root/config.ini will be lost when the container stops so make a copy of the file on persistent storage.

## 3. Upload data
The `upload_data.py` script can be used as an ingest benchmark as well as an efficient way to populate a bucket with data for late use with the `download_data.py` script. The script will look at the selected config.ini file and upload all files found in `datadir` to the bucket `bucketname` using `workers` concurrent processes.

The bucket will be created if it does not already exist. Since `download_data.py` tests raw https downloads instead of using the S3 protocol we set the permissions on the bucket and all objects to read access for anyone. In other words - do not upload files with confidential data.

```
# Start uploading data
./upload_data.py config.ini
```

## 4. Download data
The `download_data.py` script is an https random read benchmark against StorageGRID. It will first generate a list of objects in the `bucketname` bucket, randomize that list and use `workers` concurrent processes to download `number_of_objects` number of objects straight to `/dev/null`.

```
# Start downloading data
./download_data.py config.ini
```

The first version of this script used the `requests` module to download the objects, but that proved to be very cpu intensive (possibly due to my lack of understanding of that module.) Instead we now use `wget` to do the job. Despite this you will most likely run out of cpu on your Docker host before you can push StorageGRID to it's limit, even when just running against one storagenode. It should be possible to tune this further, but in my lab I just brute forced it by running the benchmark in parallel on three hosts in the Docker Swarm.

The default config.ini specifies 4 workers, but for `download_data.py` I can run 200 workers per container without any problems. You will run out of memory first so that is the thing you should watch as you increase this number.

# To be continued
So what else is there to do? I am looking at a couple of things:
* Additional tuning in `download_data.py` to lower cpu usage and get better performance per container.
* In this first version you end up with two numbers; objects/second and MB/second. It would be interresting to build a histogram or a heatmap showing the seconds/MB for each object. That would give you an idea of latencies when running many concurrent requests.
* Clean up the scripts, add comments and add some try/catch blocks to make the code more robust. ![Me producing clean code](https://media.giphy.com/media/zOvBKUUEERdNm/giphy.gif)
