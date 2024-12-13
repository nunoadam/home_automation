import yaml

def load_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
           
    devices = config.get("devices", [])
    logging_sort = config.get("logging_sort", [])
    automations = config.get("automations", [])

    return devices, logging_sort, automations