import requests

def read_device (device, client):
    """
    Read device based on device type.
    """
    try:
        if device["connection"]["type"] == "modbus":
            readings = read_modbus_device(device, client)
        elif device["connection"]["type"] == "http":
            readings = read_http_device(device)
        else:
            print(f"Unknown connection type for {device['name']}")
            return
        
        return readings
        
    except Exception as e:
        print(f"Unexpected error while logging device '{device['name']}': {e}")

def read_modbus_device(device, client):
    """
    Reads a Modbus device's metrics and returns a dictionary with the metric name and its corresponding value.
    """
    try:
        slave = device['connection']["slave"]
        method = device['connection']["method"]
        address = device['metrics'][0].get("address", 0)
        count = len(device["metrics"])

        if method == "input_register":
            response = client.read_input_registers(address=address, count=count, slave=slave)
        elif method == "holding_register":
            response = client.read_holding_registers(address=address, count=count, slave=slave)
        else:
            print(f"Unsupported Modbus method for device '{device['name']}': {method}")
            return

        if response.isError():
            print(f"Error reading Modbus device '{device['name']}'")
            return

        registers = response.registers
        readings = {}

        for i, m in enumerate(device["metrics"]):
            value = registers[i] if i < len(registers) else None

            if m.get("signed", False):
                value = value if value <= 32767 else value - 65536

            value = round(value * m.get("factor", 1), 2) if value is not None else None

            readings[m["name"]] = value

        return readings

    except Exception as e:
        print(f"Unexpected error while reading Modbus device '{device['name']}': {e}")

def read_http_device(device):
    """
    Reads an HTTP device's metrics and returns a dictionary with the metric name and its corresponding value.
    """
    try:
        url = device['connection']["url"]
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        readings = {}

        for metric in device["metrics"]:
            location = metric["location"]
            value = eval(f"data{location}")
            
            if value is not None:
                factor = metric.get("factor", 1)
                value = round(value * factor, 2)
                readings[metric["name"]] = value
            else:
                print(f"Metric '{metric['name']}' not found in device '{device['name']}'")

        return readings

    except requests.RequestException as e:
        print(f"Error reading HTTP device {device['name']}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {device['name']}: {e}")
        return None