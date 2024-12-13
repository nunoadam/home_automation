import yaml

def load_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
           
    devices = config.get("devices", [])
    automations = config.get("automations", [])

    return devices, automations