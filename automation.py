from device_reader import * 
from functions import *

def trigger (automation, devices, client):
    for i, condition in enumerate(automation["conditions"]):
        trigger = condition['trigger']
        input_device = find_object_by_name (trigger['device'], devices)
        readings = read_device (input_device, client)

        if eval ( f"{readings[trigger['metric']]}{trigger['condition']}" ):
            for action in condition['actions']:
                action_device = find_object_by_name (action['device'], devices)
                current_state, new_state = relay (action_device, action['relay'], action['state'], client)

            if current_state == new_state:
                print (f"{automation['name']}: Condition {i+1} ({trigger['metric']}: {readings[trigger['metric']]}{trigger['condition']}) meet. No changes in relay {action['relay']} (current state: {new_state})")
            else:
                print (f"{automation['name']}: Condition {i+1} ({trigger['metric']}: {readings[trigger['metric']]}{trigger['condition']}) meet. Relay {action['relay']} changed from {current_state} to {new_state})")

        else:
            print (f"{automation['name']}: Condition {i+1} ({trigger['metric']}: {readings[trigger['metric']]}{trigger['condition']}) not meet")
        
def relay (device, relay_name, new_state, client):
    try:
        if device["connection"]["type"] == "modbus":
            current_state, new_state = relay_modbus (device, relay_name, new_state, client)
        else:
            print(f"Unknown connection type for {device['name']}")
            return
        
        return current_state, new_state
        
    except Exception as e:
        print(f"Unexpected error while logging device '{device['name']}': {e}")

def relay_modbus (device, relay_name, new_state, client):
    """
    Read state of relay and returns previous state and new state
    """
    try:
        slave = device['connection']["slave"]
        method = device['connection']["method"]
        relay = find_object_by_name (relay_name , device['relays'])

        if not relay:
            print(f"Unable to find relay '{relay_name}' in device {device['name']}")
            return None, None         

        """
        Read current state
        """  

        if method == "coil":
            response = client.read_coils(address=relay["status"]["address"], count=1, slave=slave)
        else:
            print(f"Unsupported Modbus method for device '{device['name']}': {method}")
            return   
        
        if response.isError():
            print(f"Error reading Modbus device '{device['name']}'")
            return
        

        current_state_bit = response.bits[relay["status"]["bit"]]  
       
        current_state = "on" if current_state_bit else "off"
       
        """
        Change the state if needed
        """         

        if current_state != new_state:

            address = relay["address"]
            action = find_object_by_name (new_state , relay["states"])

            if method == "coil":
                response = client.write_coil(address, action, slave)
            else:
                print(f"Unsupported Modbus method for device '{device['name']}': {method}")
                return
            
            if response.isError():
                print(f"Error reading Modbus device '{device['name']}'")
                return
        
            relay_response = response.value

            new_state = "on" if relay_response else "off"

        return current_state, new_state

    except Exception as e:
        print(f"Unexpected error while reading Modbus device '{device['name']}': {e}")