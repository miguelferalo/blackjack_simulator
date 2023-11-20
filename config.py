import yaml
import os

# Load YAML file
CONFIG_FOLDER = 'config'
YAML_FILE = 'blackjack_parameters.yaml'
YAML_PATH = os.path.join(CONFIG_FOLDER, YAML_FILE)

with open(YAML_PATH, "r") as f:
    
    config_variables = yaml.load(f, Loader = yaml.loader.SafeLoader)
    