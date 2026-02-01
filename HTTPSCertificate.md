# HTTPS Certificate

*Note: these steps are for the Docker stack of EnGenius Private Cloud on Linux. I can't comment on the Windows stack*

If you want to use your own SSL certificate for the web UI, instead of the default self-signed cert, you can do so by replacing the certificate and key files for `nginx` in the `epc-api` container.

In my case, I use my own personal certificate authority within OPNSense for trust, and I created a certificate for my controller host under that CA. I then downloaded the certificate and private key as separate files, named `EPC_crt.pem` and `EPC_prv.pem`.

## 1. Copy Files
First, get those files onto the host where you have the EPC controller running. For me, that was:

``` shell
scp ~/Downloads/FitCon_*.pem epc:/tmp/
```

Then, copy those files into the `epc-api` container.

``` shell
docker cp /tmp/EPC_crt.pem epc-api:/app/nginx.crt
docker cp /tmp/EPC_prv.pem epc-api:/app/nginx.key
```

## 2. Make Changes Persistent

One of the great things about Docker is that you get a clean, known environment every time you bring up a container or image. Unfortunately, that means the customization we just did in the `epc-api` container gets lost every time you do a `./epc-prod.sh down`.

To address this, we can take a snapshot of the modified container, then update the `docker-compose.yaml` file to reference this new image instead of the default one for the `epc-api` service.

### 2.1 List Containers

List the containers and check the Container ID for the `epc-api` container.

``` shell
docker container ls | grep epc-api
```

You should see something like this, but with a different hash value in the first field:

```
fd61fdb8ae73   public.ecr.aws/d3g4m7o9/epc-api:1.8.7       "/start.sh"          32 minutes ago   Up About a minute               0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
```
### 2.2 Commit Container Changes

Then, commit the changes to the container to a new image with the name `epc-api:1.8.7-custom-01` (or whatever you like, I'm not the boss of you):

``` shell
docker commit `docker container ls | grep epc-api | awk '{print $1}'` epc-api:1.8.7-custom-01
```

### 2.3 Edit `docker-compose.yml`
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
        image: epc-api:1.8.7-custom-01
```

### 2.4 Launch Using New Image

Now you can bring down the default containers and bring up everything, but now with the new modified `epc-api` image.

``` shell
./epc-prod.sh down
./epc-prod.sh up
```