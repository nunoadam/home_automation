import numpy as np

def vpd_hpa(T, RH, altitude=657):
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

def format_readings(device, readings):
    """
    Format readings using the display string, if available.
    """
    display = device.get("display")
    readings = list(readings.values())
    if display:
        try:
            return display.format(readings=readings)
        except Exception as e:
            return f"Error formatting display for {device['name']}: {e}"
    return f"Readings for {device['name']}: {readings}"

def find_object_by_name (name, list):
    """
    Returns a device object that matches the name
    """
    for object in list:
        object = next((d for d in list if d["name"] == name), None)
        if object:
            return object
    return None

def list_devices(devices):
    """
    Lists all configured devices.
    """
    i = 0
    
    for device in devices:
        print(f'{i}: {device["type"]} : {device["name"]}')
        i += 1