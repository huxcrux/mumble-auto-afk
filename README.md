# Mumble auto AFK

Move idling users to AFK automatically

## Setup

1. Make sure your mumble server have ICE active on a TCP port

    ```ini
    ice="tcp -h 127.0.0.1 -p 6502"
    ```

2. Make sure ´icesecretwrite´ is set

    ```ini
    icesecretwrite=SUPERSECRETPASSWORD
    ```

3. Make sure you have MumbleServer.ice downloaded

    ```bash
    make prepare
    ```

4. Install dependencies

    ```bash
    pip3 install -r requirements.txt
    ```

5. Create a config file

    config.yml

    ```bash
    server:
        host: "localhost"        # Host where the Mumble server's ICE interface is listening
        port: 6502               # ICE port for the Mumble server
        server_id: 1             # Mumble virtual server ID (typically 1 unless you're using multiple servers)

    auth:
        password: "my_icesecret" # Secret used to authenticate with Mumble via ICE (from murmur.ini: IceSecretRead/IceSecretWrite)

    afk:
        idle_threshold: 300      # Time in seconds a user must be idle before being moved to the AFK channel
        afk_channel_id: 5        # The channel ID of your AFK channel (check via ICE or database)
    ```

6. Fix MumbleServes

    ```bash
    wget -O MumbleServer.ice https://raw.githubusercontent.com/mumble-voip/mumble/refs/heads/1.5.x/src/murmur/MumbleServer.ice
    slice2py MumbleServer.ice
    ```

7. Start the app

    ```bash
    python3 main.py
    ```

## Installation example for users of alliance auth mumble container

```yml
  mumble-auto-afk:
    image: ghcr.io/huxcrux/mumble-auto-afk:latest
    container_name: mumble-auto-afk # in case you run multiple containers make sure name are unique
    restart: always
    network_mode: "service:mumble_auth" # "mumble_auth" is the name if the mumble service, update if needed
    env_file:
      - ./.env # We read mumble ICE port and password from file
    environment:
      - MUMBLE_AFK_IDLE_THRESHOLD=14400 # how long the user needs to be idle in seconds
      - MUMBLE_AFK_CHANNEL_ID=1 # the ID of the AFK channel, can be seen from edit menu
    depends_on:
      - mumble_auth # "mumble_auth" is the name if the mumble service, update if needed
```

## All env vars if you wish to use them instead of a config file

```bash
MUMBLE_SERVER_HOST        = localhost
MUMBLE_ICE_PORT           = 6502
MUMBLE_SERVER_SERVER_ID   = 1
MUMBLE_ICE_SECRET         = (not set)
MUMBLE_AFK_IDLE_THRESHOLD = 300
MUMBLE_AFK_CHANNEL_ID     = 5
```
