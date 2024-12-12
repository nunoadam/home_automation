import yaml
import requests
from pymodbus.client import ModbusTcpClient

# Load devices configuration from YAML file
with open("devices.yaml", "r") as file:
    devices = yaml.safe_load(file)["modbus_devices"]

# Create Modbus client
client = ModbusTcpClient('192.168.1.200', port=4196)

def process_http_device(device):
    url = device["url"]
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        readings = []
        
        for reading in device["readings"]:
            location = reading["location"]
            try:
                value = eval(f"data{location}")  # Evaluate the JSON path dynamically
                readings.append(value)
            except KeyError:
                print(f"  - {reading['parameter']}: Path {location} not found in response")
                
        one_line_template = device.get("one_line_reading")
        if one_line_template:
            try:
                # Use the str.format method to replace placeholders dynamically
                one_line_output = one_line_template.format(readings=readings)
                print(f"{one_line_output}")
            except Exception as e:
                print(f"Error computing one-line reading for {device['name']}: {e}")
                
    except requests.RequestException as e:
        print(f"Error reading HTTP device {device['name']}: {e}")

def process_modbus_device(device):
    slave = device["address"]
    starting_address = device["starting_address"]
    count = device["number_of_registers"]
    read_method = device["read_method"]

    # Determine the appropriate reading function
    if read_method == "input_register":
        response = client.read_input_registers(address=starting_address, count=count, slave=slave)
    elif read_method == "holding_register":
        response = client.read_holding_registers(address=starting_address, count=count, slave=slave)
    else:
        print(f"Unsupported read method: {read_method} for device {device['name']}")
        return

    if not response.isError():
        registers = response.registers  # List of raw values
        readings = []
        
        for reading in device["readings"]:
            reg_id = reading["id"]
            raw_value = registers[reg_id] if reg_id < len(registers) else None
            if raw_value is not None:
                factor = reading.get("factor", 1)
                formatted_value = raw_value * factor
                units = reading.get("units", "")  # Get units if present, default to an empty string

                # Round the formatted value to 2 decimal places
                formatted_value = round(formatted_value, 2)
                readings.append(formatted_value)

            else:
                readings.append(None)  # Handle missing values

        # Compute and display one-line reading if configured
        one_line_template = device.get("one_line_reading")
        if one_line_template:
            try:
                # Use the str.format method to replace placeholders dynamically
                one_line_output = one_line_template.format(readings=readings)
                print(f"{one_line_output}")
            except Exception as e:
                print(f"Error computing one-line reading for {device['name']}: {e}")
    else:
        print(f"Error reading Modbus device: {device['name']}")

# Loop through each device and process its readings
try:
    for device in devices:
        if device["type"] == 'Energia' or device["type"] == 'Invernadero':
            if device["connection"]["type"] == "http":
                process_http_device(device)
            elif device["connection"]["type"] == "modbus":
                process_modbus_device(device)
            else:
                continue
            
finally:
    # Close Modbus client
    client.close()
