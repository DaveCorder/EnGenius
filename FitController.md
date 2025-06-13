# FitController Hacking


## Installation on Raspberry Pi (or other ARM)

### Install Prerequsites

``` shell
sudo apt install curl wget net-tools apt-transport-https ca-certificates curl gnupg lsb-release
```

### Install Docker

#### Keyring

``` shell
curl -fsSL https://download.docker.com/linux/$(lsb_release -si | tr '[:upper:]' '[:lower:]')/gpg | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

#### `apt` sources file

``` shell
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(lsb_release -si | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
```

#### `apt` install

``` shell
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io
```

### Download Install Script

``` shell
wget https://epc-release.s3.us-west-2.amazonaws.com/epc-prod.sh
chmod +x epc-prod.sh
```

#### Tweak install script

This increases the timeout the script waits for the DB to finish being initialized. The default is 1 minute - this was not sufficient on my Raspberry Pi 3 B+ (I've seen it take upwards of 30 minutes). Give it a very, very large timeout value, just to be safe.

``` shell
sed -i -e 's/^INIT_TIMEOUT=60$/INIT_TIMEOUT=60000/' epc-prod.sh
```

### Configure Network Bridge

The `epc-mdns` container uses the `host` network option for Docker. It expects, on an ARM system, to have a network interface named `br-lan` (probably because a real FitCon100 has two Ethernet ports, which I suspect are bridged together).

We need to create this bridge interface ourselves and add our Ethernet interface to it. The easiest way I found was to use NetworkManager, which will likely need to be enabled first (especially if using Raspbian).

``` shell
sudo systemctl enable systemd-networkd

sudo nmcli connection add type bridge con-name 'br-lan' ifname 'br-lan'

sudo nmcli connection add type ethernet slave-type bridge \
    con-name 'Ethernet' ifname eth0 master 'br-lan'

sudo nmcli con mod 'br-lan' ipv4.method dhcp
```

Feel free to customize the bridge as you want for your environment (static IP address, custom MAC address, etc).

### Install

The `epc-prod.sh` script takes an optional version number parameter to the `install` command. We can use that to install the 1.6.15 software for the FitCon100, which is distributed as `1.6.15-arm`.

``` shell
./epc-prod.sh install 1.6.15-arm
```

#### Note on DB Initialization

On an ARM system, it may take a _very_ long time to initialize the DB - I've seen it take upwards of 30 minutes.

Even if the installer times out on the DB initialization (with a `Need to import default data later because one or more FitCon services can not start.` message), that DB init process continues to run in the background.

You must wait for the whole DB init process to complete before continuing.

##### Monitoring DB Init

A crude but effective way to monitor the init process is to run this:

``` shell
watch "ps auwwx | grep pyc | grep -v grep"
```

You will see `db-init.pyc` come and go quite a bit. Once that stops appearing, and you see multiple instances of `/usr/local/bin/python /usr/local/bin/gunicorn ...` running, you are good to manually finish the install and continue with the next steps.

##### Finish Install

There are a couple more small DB initialization tasks that will need to be completed manually if the installer times out during the big init step. You can run the same bit of shell code the installer does to finish those tasks:

``` shell
while [ ! $(docker exec -it epc-api sh -c 'python /app/db-init.pyc -t') -eq 1 ]
do
    sleep 1
    printf "."
done
docker exec -it epc-api sh -c 'python /app/db-init.pyc -i >/dev/null 2>&1'
printf "DB Init Done\n"
```

### Post-Install Tweaks

Once the containers are installed, there's some modifications that *need* be done, and some modifications that are *nice to have*.

### Required: Remove `prestart.sh`

The `epc-api` container's startup script checks for a script at `/app/prestart.sh` and executes it if it exists. Among other things, this resets the Mongo database to its default data, which is not good (especially if you've added any custom devices). We need to nuke it.

``` shell
docker exec epc-api rm /app/prestart.sh
```

#### Required: Stop Containers

``` shell
./epc-prod.sh down
```

#### Required: Fix Missing Directory

Everything on the host OS is installed to `/epc`, however the `fitdog` script expects to find a file in `/root/fitcon/epc` instead. We just need to create a symlink for this directory.

``` shell
mkdir -p /root/fitcon ; ln -s /epc /root/fitcon/epc
```

#### Required: Fix `docker-compose.yml`

The `epc-raccoon` container is missing the `/epc` volume, so it will fail to start. We just need to add that volume to the `docker-compose.yml` file.

``` shell
nano -w /epc/pipe/docker-compose.yml
```

Find the `epc-raccoon` section.

Add `/epc` to the existing `volumes:` section (make sure the indentation matches):

``` yaml
            - /epc:/epc
```

### Required: Restart Containers

``` shell
./epc-prod up
```

### Required: Check Container Status

Wait a minute or two and then run:

``` shell
docker container ls
```

Everything should be running now. If you see anything with a Status of "restarting", that's a good indication that it had an issue during startup (the containers are set to always restart, so they'll keep trying and failing indefinitely).

### Optional: HTTPS Certificate

If you want to use your own SSL certificate for the web UI, instead of the default, you can just replace the certificate and key files for `nginx` in the `epc-api` container.

In my case, I use my own personal certificate authority within OPNSense for trust, and I created a certificate for my controller host under that CA. I then downloaded the certificate and private key as separate files, named `FitCon_crt.pem` and `FitCon_prv.pem`.

First, get those files onto the host OS. For me, that was:

``` shell
scp ~/Downloads/FitCon_*.pem fitcon:/tmp/
```

Then, copy those files into the `epc-api` container.

``` shell
docker cp /tmp/FitCon_crt.pem epc-api:/app/nginx.crt
docker cp /tmp/FitCon_prv.pem epc-api:/app/nginx.key
```

### Required: Make Changes Persistent

One of the great things about Docker is that you get a clean, known environment every time you bring up a container or image. Unfortunately, that means all the customization we just did in the `epc-api` container gets lost every time you do a `./epc-prod.sh down`.

To address this, we can take a snapshot of the modified container, then update the `docker-compose.yaml` file to reference this new image instead of the default one for the `epc-api` service.

List the containers and check the Container ID for the `epc-api` container.

``` shell
docker container ls | grep epc-api
```

You should see something like this, but with a different hash value in the first field:

```
fd61fdb8ae73   public.ecr.aws/g8k4a9z9/epc-api:1.6.15-arm       "/start.sh"          32 minutes ago   Up About a minute               0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```

Then, commit the changes to the container to a new image with the name `epc-api:1.6.15-custom-01` (or whatever you like, I'm not the boss of you):

``` shell
docker commit `docker container ls | grep epc-api | awk '{print $1}'` epc-api:1.6.15-custom-01
```

Now, edit the `docker-compose.yml` file to reference this new image:

``` shell
nano -w /epc/pipe/docker-compose.yml
```

Find these lines (should be lines 28-29):

``` yaml
    epc-api:
        image: ${REPOSITORY_URI}epc-api:${VERSION}
```

And change it to:

``` yaml
    epc-api:
        image: epc-api:1.6.15-custom-01
```

### Launch Using New Image

Now you can bring down the default containers and bring up everything, but now with the new modified `epc-api` image.

``` shell
./epc-prod.sh down
./epc-prod.sh up
```

## Backend Data Store Access

Credentials for both the MongoDB NoSQL database and the Redis key-value store are stored in plain text in the `/epc/pipe/.epc-prod` file on the host OS. Simply source this file in your shell to easily use them.

``` shell
source /epc/pipe/.epc-prod
```

### Redis

``` shell
docker exec -it epc-db /usr/bin/redis-cli -a ${REDIS_PASS}
```

### MongoDB

Two ways for this one:

Using the same credentials as the FitCon stack:

``` shell
ocker exec -it epc-db /usr/bin/mongo -u ${MONGO_USER} -p ${MONGO_PASSWORD} -authenticationDatabase admin "mongodb://127.0.0.1:27017/main"
```

Using the `__system` user backdoor:

``` shell
docker exec -it epc-db /usr/bin/mongo -u __system -p "$(tr -d '\011-\015\040' < `find /var/lib/docker -name "mongodb.key" | grep merged | head -n 1`)" --authenticationDatabase local "mongodb://127.0.0.1:27017/main"
```

## Add New Model

Each EnGenius device model has a three-character model "number" (they call it a number, but it's technically alphanumeric). This model number is embedded in each device's serial number at characters 5-7.

The FitCon software will only let you add devices to the inventory if it knows about them. There are a few EnGenius devices that inexplicably aren't in the known devices whitelist but will function perfectly well, if you can just get the controller to talk to them (example: ECS2510 and ECS2510FP, even though ECS251**2** and ECS251**2**FP are included).

There are two backend datastores for the FitCon software: MongoDB and Redis. Each has a table or object with the known models and, in the case of MongoDB, important info like device type, supported frequencey bands for APs, port count and types for switches, etc. If you wish to add a new model, both places needed to be updated.

### Add to MongoDB

There are two ways to do this, either via the mongo shell and a json description of the device, or via a Python script executed within the container. Either is fine, although the Python method should be less prone to typos and syntax errors.

#### Directly in the Mongo shell

It's as simple as this statement, provided you have the right JSON structure.

``` shell
db.models.insertOne( <JSON> );
```

##### Direct Example

The easiest way to get the JSON you need to insert is to clone a similar device and change the attributes as needed.

For example, I have some ECW230 devices flashed with the EWS377-FIT firmware. So they behave like real EWS377-FIT, but their serial numbers (stored in the nvram) are for the ECW230 series, which isn't in the supported models list.

So, to add this one, I can get the configuration for the EWS377-FIT, then modify it slightly and add the modified version to MongoDB.

``` shell
docker exec -it epc-db /usr/bin/mongo -u ${MONGO_USER} -p ${MONGO_PASSWORD} -authenticationDatabase admin "mongodb://127.0.0.1:27017/main" --eval 'db.models.findOne( { "name" : { $eq : "EWS377-FIT" } } );'
```

This should result in something like this:

```
MongoDB shell version v4.0.5
connecting to: mongodb://127.0.0.1:27017/main?authSource=admin&gssapiServiceName=mongodb
Implicit session: session { "id" : UUID("6a0cfd6b-c04c-48dd-be07-9f42a7129e9d") }
MongoDB server version: 4.0.5
{
	"_id" : ObjectId("684b1f307e0fb8109f04cfc0"),
	"type" : "ap",
	"name" : "EWS377-FIT",
	"number" : "X45",
	"band" : "2_4G|5G",
	"category" : "indoor",
	"ports" : [ ],
	"max_client_limit_24g" : 128,
	"max_client_limit_5g" : 128,
	"max_tx_power_limit_24g" : 23,
	"max_tx_power_limit_5g" : 23,
	"created_time" : ISODate("2025-06-12T18:40:47.670Z"),
	"modified_time" : ISODate("2025-06-12T18:40:47.670Z"),
	"dfs_support_type" : [
		"fcc",
		"eu"
	],
	"support_poe" : false,
	"is_support_scanning_radio" : false
}
```

Grab all the stuff after the `MongoDB server version:` line. Then:

* Remove the `"_id"` line, as it's an internally generated MongoDB identifier and we don't want to duplicate it.
* Change the `"name"` value to whatever you want
* Change the `"number"` value to the model number you are adding

Then connect to the DB and insert it into the DB:

``` shell
docker exec -it epc-db /usr/bin/mongo -u ${MONGO_USER} -p ${MONGO_PASSWORD} -authenticationDatabase admin "mongodb://127.0.0.1:27017/main"
```

```
db.models.insertOne(
{
    "type" : "ap",
    "name" : "Dummy Device",
    "number" : "XYZ",
    "band" : "2_4G|5G",
    "category" : "indoor",
    "ports" : [ ],
    "max_client_limit_24g" : 128,
    "max_client_limit_5g" : 128,
    "max_tx_power_limit_24g" : 23,
    "max_tx_power_limit_5g" : 23,
    "created_time" : ISODate("2025-06-12T18:40:47.670Z"),
    "modified_time" : ISODate("2025-06-12T18:40:47.670Z"),
    "dfs_support_type" : [
        "fcc",
        "eu"
    ],
    "support_poe" : false,
    "is_support_scanning_radio" : false
}
);
```

Then skip down to the "Sync MongoDB to Redis" section.

#### Python Example

This one is neater (IMHO) but a bit sneakier.

##### Create Script

Create a file called `add-custom-models.py`. The following is the actual script I used to add both my ECW230 and ECS2510FP devices to the `models` collection:

``` python
import os
from squirrel.mongo.mongo_connect import MongoUtil
from squirrel.models_model import Model, Port, SPEED_CAP_MAP
mongo_host = os.environ['MONGO_HOST']
mongo_db_main = os.environ['MONGO_DB_NAME']
SPEED_CAP_LIST_MAP = {'0123459': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2], SPEED_CAP_MAP[3], SPEED_CAP_MAP[4], SPEED_CAP_MAP[5], SPEED_CAP_MAP[9]], '012345': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2], SPEED_CAP_MAP[3], SPEED_CAP_MAP[4], SPEED_CAP_MAP[5]], '012': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2]]}

def add_custom_models_to_collection():
    try:
        container = mongo_host
        client = MongoUtil.mongo_connector()
        client.admin.command('ismaster')
    except Exception as e:
        return 'Error: ' + str(e.message)
    MongoUtil.mongo_connector()

    ap_ecw230_model = Model(type=Model.type_ap, name='ECW230', band='2_4G|5G', category=Model.category_indoor, number='X42', dfs_support_type=['fcc', 'eu'])
    
    switch_ecs2510fp_model = Model(type=Model.type_switch, name='ECS2510FP', number='RCF', support_poe=True)
    switch_ecs2510fp_model.ports.append(Port(id='1', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='2', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='3', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='4', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='5', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='6', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='7', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='8', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='F1', speed_cap=['auto', '1Gbps_fdx', '10Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='F2', speed_cap=['auto', '1Gbps_fdx', '10Gbps_fdx']))

    try:
        Model.objects.insert([ap_ecw230_model, switch_ecs2510fp_model])
    except Exception as e:
        print(str(e))
        raise

if __name__ == '__main__':
    add_custom_models_to_collection()
```

It *should* be fairly self-evident how the `Model` object in Python gets built and then inserted into the MongoDB collection, at least if you have a decent understanding of Python. But if you insert incorrect data, you can just go delete it from MongoDB or even reset the entire database back to the default data.

##### Copy Script

``` shell
docker cp add-custom-models.py epc-api:/tmp/
```
##### Execute Script

``` shell
docker exec epc-api python /tmp/add-custom-models.py
```

### Sync MongoDB to Redis

Once the model(s) have been added to MongoDB, they need to be synced over to the Redis instance. Fortunately there's a utility to do that for us. We just need to run it in the container:

``` shell
docker exec epc-api python /app/db-init.pyc --model
```

The `db-init.pyc` script has other interesting functionality, if you care to figure out how to dig into it.

(Actually, strictly speaking, you don't *need* to sync MongoDB to Redis, since the controller UI only relies upon the data stored in MongoDB and you can still add them manually by serial number, but the Redis side of things is used to automatically discover EnGenius devices on your network and add them to the "Pending Approval" section under "Inventory" -> "Register Devices".)
