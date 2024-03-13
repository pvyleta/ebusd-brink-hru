import os
import shutil

import sensor_data
import config_data

output_dir = "config_files"

# Manually retrieved values from various sources other than decompiling
known_values_params = {
    0x07: "0=off;1=on", # CVWTWMode
    0x08: "0=Not Permitted;1=Permitted", # UnbalanceMode
    0x0c: "0=Normally Closed;1=0-10V input;2=Normally Open;3=12V Bypass Open/0V Bypass Closed;4=0V Bypass Open/12V Bypass Closed", # Input1Mode
    0x0f: "0=off;1=on;2=on if bypass open condition satisfied;3=bypass control;4=Bedroom valve", # CN1Coupling
    0x10: "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive", # CN1Inlet
    0x11: "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive", # CN1Exhaust
    0x12: "0=Normally Closed;1=0-10V input;2=Normally Open;3=12V Bypass Open/0V Bypass Closed;4=0V Bypass Open/12V Bypass Closed", # Input2Mode
    0x15: "0=off;1=on;2=on if bypass open condition satisfied;3=bypass control;4=Bedroom valve", # CN2Coupling
    0x16: "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive", # CN2Inlet
    0x17: "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive", # CN2Exhaust
    0x18: "0=off;1=on", # EWTMode
    0x1b: "0=Auto;1=Closed;2=Open", # BypassMode
    0x31: "1=yes;0=no", # PreheaterPresent
    0x32: "1=yes;0=no", # RHSensorPresent
    0x3c: "1=yes;0=no", # CO2SensorsActivated
    0x40: "0=off;1=on", # SwitchDefaultPos
    0x41: "0=Modbus internal;1=Modbus external connect;2=External customer", # ModbusInterface
    0x43: "0=1200 Baud;1=2400 Baud;2=4800 Baud;3=9600 Baud;4=19k2 Baud;5=38k4 Baud;6=56k Baud;7=115k Baud", # ModbusSpeed
    0x44: "0=No Parity;1=Even Parity;2=Odd Parity;3=Unknown", # ModbusParity
}

# Convert the type from BrinkServiceTool to ebusd .csv file type
sensor_datatype_conversion = {
    'WordSignedValue': "SIR", 
    'WordValue': "UIR",
    'LongValue': "ULR",
    'WordTruncString': "UIR",

    # TODO this is likely wrong - word string is osmething else
    'WordString': "UIR",
}

def multiplier_to_divider(multiplier: str):
    multiplier_float = float(multiplier)
    if multiplier_float < 1:
        return str(int(1 / multiplier_float))
    elif multiplier_float > 1:
        return str(-int(multiplier_float))
    else:
        return ""

def csv_line_sensor(sensor: sensor_data.Sensor):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    values = sensor.converter.values
    type = sensor.converter.type

    return f'r,{sensor.device_lowercase},{sensor.name},{sensor.name},,,4022,{sensor.id},,,{type},{values},{sensor.unit},\n'
 
def csv_line_param_read(param: config_data.Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    if int(param.id, 16) in known_values_params:
        values = known_values_params[int(param.id, 16)]
        comment = 'This field has also "min/max/step" fields - but we skip them since we only care for the dafault'
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype_from_sign(param.is_signed)},{values},{param.unit},,,,IGN:3,,,,Default,,{datatype_from_sign(param.is_signed)},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype_from_sign(param.is_signed)},{values},{param.unit},,Max,,{datatype_from_sign(param.is_signed)},,{param.unit},,Min,,{datatype_from_sign(param.is_signed)},,{param.unit},,Step,,{datatype_from_sign(param.is_signed)},,{param.unit},,Default,,{datatype_from_sign(param.is_signed)},,{param.unit},\n'
 
def csv_line_param_write(param: config_data.Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    if int(param.id, 16) in known_values_params:
        values = known_values_params[int(param.id, 16)]
    else:
        values = multiplier_to_divider(param.multiplier)
    return f'w,{param.device_name},{param.name},{param.name},,,4080,{param.id},,,{datatype_from_sign(param.is_signed)},{values},{param.unit},\n'
 
csv_header = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'

# TODO add length checks from CMDs
def datatype_from_sign(is_signed):
    if is_signed == "true":
        return "SIR"
    elif is_signed == "false":
        return "UIR"
    else:
        raise 0
    
def csv_from_device_sensor(device_sensor):
    file_str = csv_header
    for sensor in device_sensor.sensors:
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
def write_csv_files(dict_devices_sensor, devices_param):
    shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for device in dict_devices_sensor.values():
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.sensors.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_sensor(device))

    for device in devices_param:
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.params.basic.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(device, True))
            
        with open(os.path.join(output_dir, f'{device.name}.{device.first_version}.{device.last_version}.params.plus.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(device, False))