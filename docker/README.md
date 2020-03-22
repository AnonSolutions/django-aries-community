# Install and run the Django Aries Community Demo Application

*** Note that this documentation is in active development.  If you are interested in running the demo, run the docker version.

There are two options to run the application locally - running in docker (recommended) or running all the services locally on "bare metal".


## Running Django Aries Community - Docker Version (recommended)

1. Open two bash shells, and run the following commands:

```bash
git clone https://github.com/bcgov/von-network.git
cd von-network
./manage build
./manage start
```

... and in the second shell:

```bash
git clone https://github.com/AnonSolutions/django-aries-community.git
# this is necessary only on 'nix since we are mounting local directories
chmod -R a+rwx django-aries-community/aries_community_demo
cd django-aries-community/docker
./manage start
```

That's it!  Your docker is up and running, open a browser and navigate to http://localhost:8000/

2. To shut down the environment, CTRL-C to stop the docker services and then in each shell run:

```bash
./manage rm
```

Note that you need to run this (`./manage rm`) in BOTH shells (von-network and aries-community), it's important to keep the data in both sets of docker images in sync.

3. If you want to run in "docker development" mode, then run the following command in the second shell:

```bash
./manage start-dev
```

This mounts the code from the local filesystem (instead of copying it into the docker container) so changes will get refreshed.


### Running Django Aries Community - "Bare Metal" Version

****** TODO update these steps as appropriate - note that this content is in active development, use at your own risk ******

These are basically all the steps executed to build the docker environment.

Note it is recommended to build/run on either Ubuntu 16.04 or on the latest Mac o/s.

1. Check out the following github repositories:

```bash
git clone https://github.com/hyperledger/indy-sdk.git
git clone https://github.com/bcgov/von-network.git
git clone https://github.com/ianco/indy-plenum.git
cd idy-plenum
git checkout von_network_fixes
cd ..
git clone https://github.com/anonsolutions/django-aries-community.git
```

1a. Install dependencies in von-network:

```bash
cd von-network
virtualenv --python=python3.6 venv
source venv/bin/activate
pip install -r server/requirements.txt
pip install -r server/requirements-dev.txt
```

2. In the root indy-sdk directory, build the container for the indy nodes:

```bash
cd indy-sdk
docker build -f ci/indy-pool.dockerfile -t indy_pool .
```

3. In a separate shell, install the aries-cloudagent-python dependencies:

```bash
cd django-aries-community/aries_community_demo
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Start up the indy nodes and run a postgres database:

```bash
cd indy-sdk
docker run -itd -p 9701-9708:9701-9708 indy_pool
docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres -c 'log_statement=all' -c 'logging_collector=on' -c 'log_destination=stderr'
```

5. Start up the von-network ledger browser - this also provides the capability to register DID's on the ledger for our Test organizations.  Note that you need to pass in the location of your `indy-plenum` code and the location of your `local-genesis.txt` file:

```bash
cd von-network
PYTHONPATH=<plenum location>/indy-plenum GENESIS_FILE=<genesis location>/local-genesis.txt REGISTER_NEW_DIDS=true PORT=9000 python -m server.server
```

(Note that the ledger browser uses a very limited subset of plenum code to sign the DID transactions when writing to the ledger.  You can try installing plenum via pip if you like, although the dependencies are fairly complicated.)

6. Initialize the environment and setup test agents:

```bash
cd django-aries-community/aries_community_demo
./reload_db.sh
./init_data.sh
```

7. Finally run the django server:

```bash
python manage.py runserver
```

### Reset the Django Aries Community environment

To reset the environment and start from scratch:

1. Shut down the von-network ledger browser (just CRTL-C to kill this process)

2. Kill the 2 docker processes (indy nodes and postgres database):

```bash
docker ps -a -q | xargs docker rm -f
rm -rf ~/.indy_client/
```

To re-start the environment, just go to step #4 of the previous section.

