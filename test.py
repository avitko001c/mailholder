import argparse

from configman import ConfigMan


class LoggingConfig(ConfigMan):
    log_level: str = "error"


class Config(ConfigMan):
    port: int
    logging: LoggingConfig


config = Config()
parser = argparse.ArgumentParser()

config.port = 443
config.set_auto_env("MY_PROGRAM")
config.set_env("logging.log_level", "LOG_LEVEL")
config.set_config_file("config.json")
config.set_arg("logging.log_level", "--log_level", "-l", parser)

args = parser.parse_args()

config.load(args)
