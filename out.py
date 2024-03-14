import os
import shutil

import sensor_data
import config_data
import dev

output_dir = "config_files"

def multiplier_to_divider(multiplier: str):
    multiplier_float = float(multiplier)
    if multiplier_float < 1:
        return str(int(1 / multiplier_float))
    elif multiplier_float > 1:
        return str(-int(multiplier_float))
    else:
        return ""
    
# TODO Add original min/max/step/default as a comment to fields
def csv_line_sensor(sensor: sensor_data.Sensor):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    values = sensor.converter.values
    type = sensor.converter.type

    return f'r,{sensor.device_name},{sensor.name_current.removeprefix('Current')},{sensor.name_description},,,4022,{sensor.id},,,{type},{values},{sensor.unit},\n'
 
def csv_line_param_read(param: config_data.Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = datatype_from_sign(param.is_signed)
    if values := param.values:
        comment = '"min/max/step" fields of this enum message omitted'
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype},{values},{param.unit},,,,IGN:3,,,,Default,,{datatype},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype},{values},{param.unit},,Max,,{datatype},,{param.unit},,Min,,{datatype},,{param.unit},,Step,,{datatype},,{param.unit},,Default,,{datatype},,{param.unit},\n'
 
def csv_line_param_write(param: config_data.Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = datatype_from_sign(param.is_signed)
    if values := param.values:
        pass
    else:
        values = multiplier_to_divider(param.multiplier)
    return f'w,{param.device_name},{param.name},{param.name},,,4080,{param.id},,,{datatype},{values},{param.unit},\n'
 
csv_header = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'

# TODO add length checks from CMDs
def datatype_from_sign(is_signed):
    if is_signed == "true":
        return "SIR"
    elif is_signed == "false":
        return "UIR"
    else:
        raise 0
    
def csv_from_sensors(sensors):
    file_str = csv_header
    for sensor in sensors:
        file_str += csv_line_sensor(sensor)
    return file_str

def csv_from_device_param(device_param, is_basic):
    if is_basic:
        params = device_param.params[0:int(device_param.params_basic)]
    else:
        params = device_param.params[0:int(device_param.params_plus)]

    file_str = csv_header
    for param in params:
        file_str += csv_line_param_read(param)
        if not param.is_read_only:
            file_str += csv_line_param_write(param)
    return file_str

# TODO Add comment to converters that were filled manually
# Contents of output_dir are always cleaned before writing
# File format is [device_name].[lowest_sw_version].[highest_sw_version].[params|sensors.basic|sensors.plus].csv
def write_csv_files(dict_devices_sensor: dict[dev.Device, list[sensor_data.Sensor]], device_parameters: list[config_data.DeviceParameters]):
    shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for device, sensors in dict_devices_sensor.items():
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.sensors.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_sensors(sensors))

    for device in device_parameters:
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.params.basic.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(device, True))
            
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.params.plus.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(device, False))