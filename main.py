#!/usr/bin/env python3
import os
import sys
import time
import yaml
import logging
import Ice
import Murmur

CONFIG_PATH = "config.yml"
MAX_RETRIES = 10
RETRY_DELAY = 10
CHECK_INTERVAL = 60  # seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def load_config(path=CONFIG_PATH):
    required_keys = {
        "server": ["host", "port", "server_id"],
        "auth": ["password"],
        "afk": ["idle_threshold", "afk_channel_id"],
    }

    config_data = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            config_data = yaml.safe_load(f) or {}

    # Custom ENV mappings
    env_override_map = {
        ("server", "port"): "MUMBLE_ICE_PORT",
        ("auth", "password"): "MUMBLE_ICE_SECRET",
        ("afk", "afk_channel_id"): "MUMBLE_AFK_CHANNEL_ID",
    }

    # Defaults
    defaults = {
        ("server", "host"): "localhost",
        ("server", "server_id"): 1,
    }

    def get_env_override(section, key):
        env_key = env_override_map.get((section, key), f"MUMBLE_{section.upper()}_{key.upper()}")
        return os.getenv(env_key)

    final_config = {}
    for section, keys in required_keys.items():
        final_config[section] = {}
        for key in keys:
            raw_val = get_env_override(section, key)
            if raw_val is None:
                raw_val = config_data.get(section, {}).get(key)
            if raw_val is None:
                raw_val = defaults.get((section, key))
            if raw_val is None:
                raise ValueError(f"Missing required config value: {section}.{key}")

            if key in ["port", "server_id", "idle_threshold", "afk_channel_id"]:
                try:
                    raw_val = int(raw_val)
                except ValueError:
                    raise ValueError(f"Invalid integer for {section}.{key}: {raw_val}")

            final_config[section][key] = raw_val

    return final_config

def setup_ice_connection(config):
    props = Ice.createProperties([])
    props.setProperty("Ice.ImplicitContext", "Shared")
    props.setProperty("Ice.MessageSizeMax", "65535")
    props.setProperty("Ice.Default.EncodingVersion", "1.0")

    idata = Ice.InitializationData()
    idata.properties = props
    communicator = Ice.initialize(idata)
    communicator.getImplicitContext().put("secret", config["auth"]["password"])

    proxy = communicator.stringToProxy(f'Meta:tcp -h {config["server"]["host"]} -p {config["server"]["port"]}')
    meta = Murmur.MetaPrx.checkedCast(proxy)
    if not meta:
        raise RuntimeError("Invalid Meta proxy.")
    return communicator, meta.getServer(config["server"]["server_id"])

def reconnect_with_retry(config):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.info(f"Attempting to connect to server (attempt {attempt}/{MAX_RETRIES})")
            return setup_ice_connection(config)
        except Exception as e:
            logging.warning(f"Connection attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Failed to reconnect after multiple attempts.")
                sys.exit(1)

def main():
    try:
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    communicator, server = reconnect_with_retry(config)

    afk_channel_id = config["afk"]["afk_channel_id"]
    idle_threshold = config["afk"]["idle_threshold"]

    logging.info("Starting AutoAFK loop.")
    while True:
        try:
            users = server.getUsers()
            for user in users.values():
                if user.channel != afk_channel_id and user.idlesecs > idle_threshold:
                    logging.info(f"Moving '{user.name}' to AFK (idle {user.idlesecs}s)")
                    user.channel = afk_channel_id
                    server.setState(user)
        except Exception as e:
            logging.warning(f"Connection error: {e}. Attempting to reconnect...")
            try:
                if communicator.isAlive():
                    communicator.destroy()
            except:
                pass
            communicator, server = reconnect_with_retry(config)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
