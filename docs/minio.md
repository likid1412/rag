# Minio as local storage

## Deploy with docker

Please follow the official doc below to deploy minio:

[Deploy MinIO: Single-Node Single-Drive — MinIO Object Storage for Container](https://min.io/docs/minio/container/operations/install-deploy-manage/deploy-minio-single-node-single-drive.html)

Here is some important steps:

```sh
# pull image
docker pull quay.io/minio/minio

# run in
docker run -dt \
  -p 9000:9000 -p 9001:9001 \
  -v your_path/minio/data:/mnt/data \
  -v your_path/minio/config.env:/etc/config.env \
  -e "MINIO_CONFIG_ENV_FILE=/etc/config.env" \
  --name "minio_local"                          \
  quay.io/minio/minio server --console-address ":9001"

# check minio deployed successful
docker logs minio_local

```

You can access minio with `http://localhost:9001` in host machine.

## ENDPOINT, ACCESS_KEY and SECRET_KEY

Once deployed success, you will need ENDPOINT, ACCESS_KEY and SECRET_KEY to access minio using minio sdk.

### ENDPOINT

- The default minio endpoint is `http://localhost:9000`, you can access it in your host machine.
- There are two docker containers the We have deployed, rag and minio_local, we need to access minio_local in rag, so we need to get the minio_local container, run command below will get the ip such as `192.168.215.3`, so the **ENDPOINT** is `192.168.215.3:9090`

```sh
# if you follow the official doc, the container_name should be minio_local
docker inspect minio_local | grep IPAddress | cut -d '"' -f 4

# or use your own container name or id
docker inspect <container_name_or_id> | grep IPAddress | cut -d '"' -f 4
```

- The **ENDPOINT** will use in rag when using the minio sdk to access minio_local, set it to `MINIO_ENDPOINT` in `rag/.env`

### ACCESS_KEY and SECRET_KEY

- Find them in [MinIO Console](http://localhost:9001/access-keys)
- Set to `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in `rag/.env`

## Python SDK

Check the python sdk for developing. We will use the `put_object` and `presigned_get_object` to upload and get download url.

[Python Quickstart Guide — MinIO Object Storage for Linux](https://min.io/docs/minio/linux/developers/python/minio-py.html#example-file-uploader)

## mc command line tool (Optional)

Try minio client to list files in bucket, first need to install it.

[MinIO Client — MinIO Object Storage for Linux](https://min.io/docs/minio/linux/reference/minio-mc.html)

```sh
curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  --create-dirs \
  -o $HOME/minio-binaries/mc

chmod +x $HOME/minio-binaries/mc
export PATH=$PATH:$HOME/minio-binaries/

mc --help

# for play.min.io which deployed by minio in cloud, default set in mc tool
mc ls play/python-test-bucket

# set your local minio which you just deployed in local
mc alias set myminio http://$MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
mc admin info myminio
# list files in test bucket, you can create bucket using browser http://localhost:9001
mc ls myminio/test
```
