import time
import os
import csv

def csv_writer(device, readings):
    """
    Write log file with readings in the updated format.

    Args:
        device (dict): Device information containing "name" and "metrics".
        readings (dict): Dictionary containing metric names and their values.
    """
    data = []
    timestamp = round(time.time())

    for metric_name, value in readings.items():
        data.append(
            {
                'timestamp': timestamp,
                'device': device["name"],
                'metric': metric_name,
                'value': value
            }
        )

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