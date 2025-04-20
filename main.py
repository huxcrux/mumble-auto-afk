#!/usr/bin/env python3
import Ice
import time
import yaml
import MumbleServer
import sys
import os
import logging
from datetime import datetime

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Load YAML config ---
def load_config(path="config.yml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    required = {
        "server": ["host", "port", "server_id"],
        "auth": ["password"],
        "afk": ["idle_threshold", "afk_channel_id"],
    }

    for section, keys in required.items():
        if section not in config:
            raise ValueError(f"Missing section '{section}' in config.")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing key '{section}.{key}' in config.")

    return config

# --- Apply ENV overrides ---
def override_with_env(config):
    def get_env(section, key, cast=str):
        env_key = f"MUMBLE_{section.upper()}_{key.upper()}"
        if env_key in os.environ:
            try:
                return cast(os.environ[env_key])
            except Exception:
                raise ValueError(f"Invalid value for {env_key}")
        return config[section][key]

    return {
        "server": {
            "host": get_env("server", "host"),
            "port": get_env("server", "port", int),
            "server_id": get_env("server", "server_id", int),
        },
        "auth": {
            "password": get_env("auth", "password"),
        },
        "afk": {
            "idle_threshold": get_env("afk", "idle_threshold", int),
            "afk_channel_id": get_env("afk", "afk_channel_id", int),
        },
    }

# --- AutoAFK core logic ---
class AutoAFK:
    def __init__(self, server, afk_channel_id, idle_threshold):
        self.server = server
        self.afk_channel_id = afk_channel_id
        self.idle_threshold = idle_threshold

    def run(self):
        logging.info("AutoAFK monitoring started, will check for idle users once a minute")
        while True:
            users = self.server.getUsers()
            for session, user in users.items():
                if user.channel != self.afk_channel_id and user.idlesecs > self.idle_threshold:
                    logging.info(f"Moved user '{user.name}' to AFK (idle {user.idlesecs}s).")
                    user.channel = self.afk_channel_id
                    self.server.setState(user)
            time.sleep(60)

# --- Main entrypoint ---
def main():
    try:
        config = override_with_env(load_config())

        host = config["server"]["host"]
        port = config["server"]["port"]
        server_id = config["server"]["server_id"]
        password = config["auth"]["password"]
        afk_channel_id = config["afk"]["afk_channel_id"]
        idle_threshold = config["afk"]["idle_threshold"]

        # Set Ice properties
        props = Ice.createProperties([])
        props.setProperty("Ice.ImplicitContext", "Shared")
        props.setProperty("Ice.MessageSizeMax", "65535")
        props.setProperty("Ice.Default.EncodingVersion", "1.0")

        idata = Ice.InitializationData()
        idata.properties = props
        ice = Ice.initialize(idata)

        # Set shared secret for authentication
        ice.getImplicitContext().put("secret", password)


        # Connect to Meta interface
        proxy = ice.stringToProxy(f'Meta:tcp -h {host} -p {port}')
        meta = MumbleServer.MetaPrx.checkedCast(proxy)

        if not meta:
            raise RuntimeError("Failed to connect: invalid Meta proxy.")

        try:
            server = meta.getServer(server_id)
        except MumbleServer.InvalidSecretException:
            logging.error("Invalid Ice secret (check murmur.ini icesecretwrite or icesecretread).")
            sys.exit(1)

        afk = AutoAFK(server, afk_channel_id, idle_threshold)
        afk.run()

    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
