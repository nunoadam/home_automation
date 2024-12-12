from pymodbus.client import ModbusTcpClient
import os
import numpy as np

from csv_writer import *
from functions import *
from device_reader import *
from config_loader import *
from automation import *

def log_device(device, client):
    """
    Logs readings and displays formatted value.
    """
    try:
        readings = read_device(device, client)
        
        if readings:
            try:
                csv_writer(device, readings)
            except Exception as e:
                print(f"Error writing csv '{device['name']}': {e}")

            print(format_readings(device, readings))
        
    except Exception as e:
        print(f"Unexpected error while logging device '{device['name']}': {e}")

def log_all(client, logging_sort):
    """
    Run logging in the order defined in logging_configuration.
    """

    for section in logging_sort:
        for device_type, logs in section.items():
            print(f'----- {device_type} -----')
            if device_type == 'Invernadero' or device_type == 'Energia':
                for log in logs:
                    device = find_object_by_name (log, devices)
                    if device:
                        log_device(device, client)
                        continue
                    else:
                        print(f"Device '{log}' not found!")
            elif device_type == 'Acciones':
                for log in logs:
                    automation = find_object_by_name (log, automations)
                    if automation:
                        print(automation["name"])
                        continue
                    else:
                        print(f"Device '{log}' not found!")
            else:
                print(f"Unkown '{device_type}' section!")

                    
if __name__ == "__main__": 

    client = ModbusTcpClient("192.168.1.200", port=4196)

    devices, logging_sort, automations, derived_metrics = load_config()
    
    os.system("clear")

    try:
        log_all(client, logging_sort)
    finally:
        client.close()
