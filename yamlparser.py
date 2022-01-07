import yaml
#from os import environ
import logging

_LOGGER = logging.getLogger(__name__)


def load_yaml(file):
    try:
        stram = open(file, "r")
        yaml_data = yaml.load(stram, Loader=yaml.SafeLoader)
        return yaml_data
    except Exception as e:
        _LOGGER.error("Cannot load config file")
        raise
