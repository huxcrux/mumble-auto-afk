# Mumble auth AFK

Move idleing users to AFK automaticly

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
        host: 127.0.0.1
        port: 6502
        server_id: 1

    auth:
        password: supersecretpass

    afk:
        idle_threshold: 30
        afk_channel_id: 1
    ```

6. Start the app

    ```bash
    python3 main.py
    ```
