import csv
import time
import os
import requests
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import numpy as np
import ctypes

client = ModbusTcpClient('192.168.1.200', port=4196)

def calculate_vpd_hpa(T, RH, altitude=657):
    """
    Calculate VPD (Vapor Pressure Deficit) in hPa.
    """
    e_sat = 6.1078 * np.exp((17.269 * T) / (T + 237.3))  # Saturated vapor pressure in hPa
    e_air = e_sat * (RH / 100)  # Actual vapor pressure in hPa

    # Adjust for altitude
    p_air = 1013.25 * (1 - 0.0065 * altitude / 288.15)**5.255  # Pressure at altitude in hPa
    e_sat_site = e_sat * (p_air / 1013.25)
    e_air_site = e_air * (p_air / 1013.25)

    vpd = e_sat_site - e_air_site  # VPD in hPa
    
    return float(vpd)  # Return VPD as a float

def csv_writer(data):

    date_str = time.strftime('%Y%m%d', time.localtime())

    save_path = f'csv/{date_str[0:6]}'

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    csv_file_path = f'{save_path}/{date_str}.csv'

    file_exists = os.path.isfile(csv_file_path)

    with open(csv_file_path, mode='a', newline='') as csvfile:
        fieldnames = ['timestamp', 'device', 'metric', 'value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()        

        for row in data:
            writer.writerow(row)

def read_modbus_registers(address, count, slave, mode = 'input_registers'):
    try:
        
        if mode == 'input_registers':
            result = client.read_input_registers(address=address, count=count, slave=slave)
        elif mode == 'holding_registers':
            result = client.read_holding_registers(address=address, count=count, slave=slave)
        else:
            raise Exception(f"Unknown mode: {mode}")
        
        if result.isError():
            raise Exception(f"Modbus error: {result}")
        return result.registers
    except Exception as e:
        print(f"Error reading registers from slave {slave}: {e}")
        return None

def log_shelly_em():

    try:

        status = requests.get("http://192.168.0.65/status").json()

        data = [
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 0', 'metric': 'power', 'value': status['emeters'][0]['power']},
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 0', 'metric': 'total', 'value': status['emeters'][0]['total']},
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 0', 'metric': 'total_returned', 'value': status['emeters'][0]['total_returned']},
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 1', 'metric': 'power', 'value': status['emeters'][1]['power']},
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 1', 'metric': 'total', 'value': status['emeters'][1]['total']},
                {'timestamp': status['unixtime'], 'device': 'Shelly PM 1', 'metric': 'total_returned', 'value': status['emeters'][1]['total_returned']}
            ]

        csv_writer(data)

        return f"Home energy: {status['emeters'][0]['power']}W"
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"
    except KeyError as e:
        return f"Missing key in response: {e}"
    
def log_shelly_calefactor_armario():

    try:

        status = requests.get("http://192.168.0.32/rpc/Shelly.GetStatus").json()
        
        power = status['switch:0']['apower']

        data = [
                {'timestamp': round(time.time()), 'device': 'Calefactor armario', 'metric': 'power', 'value': power}
            ]

        csv_writer(data)

        return f"Calefactor armario: {power}W"
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"
    except KeyError as e:
        return f"Missing key in response: {e}"

def log_humedad_suelo():

    try:

        sonda = 'humedad suelo'
        readings = read_modbus_registers (address=0, count=3, slave=1)

        if readings:

            data = [
                    {'timestamp': round(time.time()), 'device': sonda, 'metric': 'temperature', 'value': readings[0] / 100},
                    {'timestamp': round(time.time()), 'device': sonda, 'metric': 'humidity', 'value': readings[1] / 100},
                    {'timestamp': round(time.time()), 'device': sonda, 'metric': 'ec', 'value': readings[2]}
                ]
        
            csv_writer(data)
            
            global temperatura_suelo
            
            temperatura_suelo = readings[0] / 100

            return f'Humedad suelo: {readings[0] / 100}°C, {readings[1] / 100}% HR'
        
        else:
            return "Failed to read pH sensor data"
    
    except Exception as e:
        return f"Exception occurred: {e}"
       
def log_sensor_ph():

    try:

        sonda = 'pH'
        readings = read_modbus_registers(address=0, count=1, slave=2)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'pH', 'value': readings[0] / 10}
            ]
        
        csv_writer(data)

        return f'pH: {readings[0] / 10}'
    
    except Exception as e:
        return f"Exception occurred: {e}"

def log_sensor_npk():

    try:

        sonda = 'NPK'
        readings = read_modbus_registers(address=0, count=3, slave=3)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'N', 'value': readings[0]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'P', 'value': readings[1]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'K', 'value': readings[2]}
            ]

        csv_writer(data)

        return f'NPK: {readings[0]}-{readings[1]}-{readings[2]}'
    
    except Exception as e:
        return f"Exception occurred: {e}"

def log_sensor_suelo():

    try:

        sonda = 'suelo'
        readings = read_modbus_registers(address=0, count=9, slave=4)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'humidity', 'value': readings[0]/10},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'temperature', 'value': readings[1]/10},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'ec', 'value': readings[2]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'pH', 'value': readings[3]/10},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'N', 'value': readings[4]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'P', 'value': readings[5]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'K', 'value': readings[6]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'salinity', 'value': readings[7]},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'tds', 'value': readings[8]}
            ]

        csv_writer(data)

        return f'Suelo: {readings[1] / 10}°C, {readings[0] / 10}% HR, {readings[4]}-{readings[5]}-{readings[6]} pH:{readings[3]/10}'
    
    except Exception as e:
        return f"Exception occurred: {e}"

def log_sensor_temperatura_interior():

    try:

        sonda = 'temp_interior'
        readings = read_modbus_registers(address=0, count=2, slave=5)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'humidity', 'value': readings[0]/10},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'temperature', 'value': readings[1]/10},
            ]

        csv_writer(data)
        
        global temperatura_interior
        global humedad_interor
        
        temperatura_interior = readings[1]/10
        humedad_interor = readings[0]/10

        return f'Temp interior: {readings[1] / 10}°C, {readings[0] / 10}% HR'

    except Exception as e:
        return f"Exception occurred: {e}"
    
def log_sensor_temperatura_exterior():

    try:

        sonda = 'temp_exterior'
        readings = read_modbus_registers(address=0, count=2, slave=6)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'humidity', 'value': readings[0]/10},
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'temperature', 'value': readings[1]/10},
            ]

        csv_writer(data)

        return f'Temp exterior: {readings[1] / 10}°C, {readings[0] / 10}% HR'
    
    except Exception as e:
        return f"Exception occurred: {e}"  
    
def log_sensor_co2():

    try:

        sonda = 'co2'
        readings = read_modbus_registers(address=0, count=1, slave=7)

        data = [
                {'timestamp': round(time.time()), 'device': sonda, 'metric': 'co2', 'value': readings[0]}
            ]

        csv_writer(data)

        return f'Nivel CO2: {readings[0]} ppm'
    
    except Exception as e:
        return f"Exception occurred: {e}"  

def log_energia_paneles_solares():

    def decode_float_from_registers(registers, start_index):
        decoder = BinaryPayloadDecoder.fromRegisters(registers[start_index:start_index+2], byteorder=Endian.Big, wordorder=Endian.Big)
        return float('{0:.2f}'.format(decoder.decode_32bit_float()))

    try:

        sonda = 'solar'

        registers = client.read_holding_registers(address=4, count=18, slave=227).registers

        activePower = decode_float_from_registers(registers, 0)
        reactivePower = decode_float_from_registers(registers, 2)
        apparentPower = decode_float_from_registers(registers, 4)
        powerFactor = decode_float_from_registers(registers, 6)
        importActiveEnergy = decode_float_from_registers(registers, 8)
        exportActiveEnergy = decode_float_from_registers(registers, 10)
        importReactiveEnergy = decode_float_from_registers(registers, 12)
        exportReactiveEnergy = decode_float_from_registers(registers, 14)

        registers = read_modbus_registers(address=514, count=1, slave=227, mode = 'holding_registers')
 
        power = ctypes.c_int16(registers[0]).value*10

        data = [
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'activePower', 'value': activePower},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'reactivePower', 'value': reactivePower},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'apparentPower', 'value': apparentPower},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'powerFactor', 'value': powerFactor},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'importActiveEnergy', 'value': importActiveEnergy},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'exportActiveEnergy', 'value': exportActiveEnergy},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'exportReactiveEnergy', 'value': importReactiveEnergy},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'exportReactiveEnergy', 'value': exportReactiveEnergy},
                {'timestamp': round(time.time()), 'device': 'solar panels', 'metric': 'power', 'value': power}
            ]
        
        csv_writer(data)

        return f'Solar: {power}W'
    
    except Exception as e:
        return f"Exception occurred: {e}"
    
def adjust_soil_heater (temp, t_min, t_max):     
    
    calefactor_1 = client.read_coils(address=0, count=1, slave=16).bits[0]
      
    def control_heater(state):
        try:
            result = client.write_coil(0, state, slave=16)
            if result.isError():
                raise Exception(f"Modbus error: {result}")
            return result.value
        except Exception as e:
            print(f"Error reading registers from slave 16: {e}")
            return calefactor_1  
        
    previous_state =  calefactor_1
           
    if (temp > t_max):
        calefactor_1 = control_heater(False)
    elif (temp < t_min):
        calefactor_1 = control_heater(True)
        
    status = 'Encendido' if calefactor_1 else 'Apagado'
    
    if calefactor_1 != previous_state:
        data = [{
            'timestamp': round(time.time()),
            'device': 'calefactor de suelo 1',
            'metric': 'action',
            'value': 1 if calefactor_1 else 0
        }]
        csv_writer(data)                
        return f'{status} del calefactor 1'
         
    return f'Calefactor 1 {status.lower()}, temperatura {temp}°C'

def adjust_fan_1(hum, temp):
    
    vpd_hpa = calculate_vpd_hpa (temp, hum)
    
    ventilador_1 = client.read_coils(address=0, count=1, slave=16).bits[1]  
    ventilador_2 = requests.get('http://192.168.1.101/relay/0?status').json()['ison']

    def control_fan(state):
        try:
            result = client.write_coil(1, state, slave=16)
            if result.isError():
                raise Exception(f"Modbus error: {result}")
            return result.value
        except Exception as e:
            print(f"Error reading registers from slave 16: {e}")
            return ventilador_1    
        
    previous_state_1 = ventilador_1
    previous_state_2 = ventilador_2
    
    if vpd_hpa < 4:
        ventilador_1 = control_fan(True)
        ventilador_2 = requests.get('http://192.168.1.101/relay/0?turn=on').json()['ison']
    if temp > 25:
        ventilador_1 = control_fan(True)
        ventilador_2 = requests.get('http://192.168.1.101/relay/0?turn=on').json()['ison']
    elif vpd_hpa > 6:
        ventilador_1 = control_fan(False)
        ventilador_2 = requests.get('http://192.168.1.101/relay/0?turn=off').json()['ison']

    status_1 = 'Encendido' if ventilador_1 else 'Apagado'
    status_2 = 'Encendido' if ventilador_2 else 'Apagado'
       
    if ventilador_1 != previous_state_1:
        data = [{
            'timestamp': round(time.time()),
            'device': 'ventilador 1',
            'metric': 'action',
            'value': 1 if ventilador_1 else 0
        }]
        csv_writer(data)            
        

    if ventilador_2 != previous_state_2:
        data = [{
            'timestamp': round(time.time()),
            'device': 'ventilador 2',
            'metric': 'action',
            'value': 1 if ventilador_2 else 0
        }]
        csv_writer(data)                 
   
    if ventilador_1 != previous_state_1:
        if ventilador_2 == previous_state_2:
            return f'{status_1} del ventilador 1'
        elif ventilador_2 != previous_state_2:
            return f'{status_1} del ventilador 1 y {status_2} del ventilador 2'
    elif ventilador_1 == previous_state_1:
        if ventilador_2 == previous_state_2:
            return f'Ventilador 1 {status_1.lower()}, ventilador 2 {status_2.lower()}, temperatura {temp}°C, humedad {hum}%, DPV {str(round(vpd_hpa, 2))} hPa'
        elif ventilador_2 != previous_state_2:
            return f'{status_2} del ventilador 2'
    
def run_all():

    print('----- energia -----')

    print(log_shelly_em())
    print(log_energia_paneles_solares())
    print(log_shelly_calefactor_armario())

    print('----- invernadero -----')

    print(log_humedad_suelo())
    print(log_sensor_ph())
    print(log_sensor_npk())
    print(log_sensor_suelo())
    print(log_sensor_temperatura_interior())
    print(log_sensor_temperatura_exterior())
    print(log_sensor_co2())

    print('----- acciones -----')
    
    try:
        print(adjust_soil_heater(temperatura_suelo,16,19))
    except:
        print('Error al ajustar calefactor del suelo')
        
    try:
        print(adjust_fan_1(humedad_interor, temperatura_interior))
    except:
        print('Error el ventilador 1')

try:
    while True:
       os.system("clear")
       run_all()
       time.sleep(60)

except KeyboardInterrupt:
    print("Data collection stopped by user.")

finally:
    client.close()
