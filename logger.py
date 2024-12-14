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
                csv_writer(device["name"], readings)
            except Exception as e:
                print(f"Error writing csv '{device['name']}': {e}")

            print(format_readings(device, readings))
        
    except Exception as e:
        print(f"Unexpected error while logging device '{device['name']}': {e}")

def log_all(client, devices, automations):
    """
    Run logging
    """
    print ('----- Energia -----')
    log_category ('Energia', client, devices)
    print ('----- Invernadero -----')
    log_category ('Invernadero', client, devices)
    print ('----- Otros -----')
    log_category ('Otros', client, devices)
    print ('----- Acciones -----')
    for automation in automations:
        print(automation['name'])
        trigger (automation, devices, client)

def log_category (category, client, devices):
    for device in devices:
        if device['category'] == category and device['enabled'] and device['type'] == 'sensor':
            try:
                log_device(device, client)
            except Exception as e:
                print(f"Unexpected error for {device['name']}: {e}")
                    
if __name__ == "__main__": 

    client = ModbusTcpClient("192.168.1.200", port=4196)

    try:
        while True:
            os.system("clear")
            devices, automations = load_config()
            log_all(client, devices ,automations)
            time.sleep(60)

    except KeyboardInterrupt:
        print("Data collection stopped by user.")

    finally:
        client.close()
