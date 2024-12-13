from device_reader import * 
from functions import *

def trigger (automation, devices, client):
    for i, condition in enumerate(automation["conditions"]):

        trigger = condition['trigger']
        input_device = find_object_by_name (trigger['device'], devices)

        readings = read_device (input_device, client)

        if trigger['metric'].upper() == 'VPD':
            vpd = vpd_hpa (readings['temperature'], readings['humidity'])
            readings['VPD'] = round(vpd, 2)
              
        if eval ( f"{readings[trigger['metric']]}{trigger['condition']}" ):
            print (f"\t{input_device['name']}, {trigger['metric']}: {readings[trigger['metric']]} Condition meet ({trigger['condition']})")
            for action in condition['actions']:
                action_device = find_object_by_name (action['device'], devices)
                current_state, new_state = relay (action_device, action['relay'], action['state'], client)

            if current_state == new_state:
                print (f"\t\tNo changes in relay {action['relay']} (current state: {new_state})")
            else:
                print (f"\t\tRelay {action['relay']} changed from {current_state} to {new_state})")

        else:
            print (f"\t{input_device['name']}, {trigger['metric']}: {readings[trigger['metric']]} Condition not meet ({trigger['condition']})")
        
def relay (device, relay_name, new_state, client):
    try:
        if device["connection"]["type"] == "modbus":
            current_state, new_state = relay_modbus (device, relay_name, new_state, client)
        elif device["connection"]["type"] == "http":
            current_state, new_state = relay_http (device, relay_name, new_state)
        else:
            print(f"Unknown connection type for {device['name']}")
            return
        
        return current_state, new_state
        
    except Exception as e:
        print(f"Unexpected error while logging device '{device['name']}': {e}")

def relay_http (device, relay_name, new_state):
    """
    Read state of relay and returns previous state and new state
    """
    try:
        url = device['connection']["url"]
        relay = find_object_by_name (relay_name , device['relays'])

        if not relay:
            print(f"Unable to find relay '{relay_name}' in device {device['name']}")
            return None, None         

        """
        Read current state
        """  
        response = requests.get(f"{url}{relay['status']['location']}", timeout = 3)
        response.raise_for_status() 
      
        current_state_bit = response.json()['ison']
      
        current_state = "on" if current_state_bit else "off"
       
        """
        Change the state if needed
        """         

        if current_state != new_state:

            response = requests.get(f"{url}turn={new_state}", timeout = 3)

            response.raise_for_status()            

            relay_response = response.json()['ison']

            new_state = "on" if relay_response else "off"

        return current_state, new_state

    except requests.exceptions.Timeout:
        print("The request timed out. Please try again later.")
        return None

    except requests.RequestException as e:
        print(f"Error reading HTTP device {device['name']}: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error while reading Modbus device '{device['name']}': {e}")

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
            action = True if new_state == "on" else False

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