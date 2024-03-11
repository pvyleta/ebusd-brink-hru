import os
import shutil

import sensor_data

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

# Manually retrieved values from various sources other than decompiling
# Note: The naming is a bit off, they do not apply to Elan and Flair in all cases, and sometimes are incomplete.
manual_values_sensors = {
    0x01: "0=Min;1=Low;2=Medium;3=High", # FanMode
    0x0e: "0=Initialize;1=Opening;2=Closing;3=Open;4=Closed;5=Error;255=Unknown", # BypassStatus
    0x0f: "0=Initialize;1=Disabled;2=Enabled;3=Testmode;255=Unknown", # PreheaterStatus
    0x11: "0=Initialize;1=Const. Flow;2=Const. RPM;3=Off;4=Error", # FanStatus
    0x16: "0=Initialize;1=No Frost;2=Defrost Wait;3=Heater;4=Error;5=Velu Heater;6=Velu Unbalance;7=Unbalanace", # FrostStatus
    0x18: "0=Clean;1=Dirty", # FilterStatus
    0x1d: "0=Initialize;1=Disabled;2=Enabled", # PostheaterStatus
    0x1f: "2=Precool;1=Disabled;0=Preheat", # EWTStatus
    0x21: "0=Error;1=Not Initialized;2=Sensor Not Active;3=PowerUp Delay;4=Normal RH;5=Boost Rising;6=Boost Stable;7=Boost Decending", # HumidityBoostState
}

# Convert the type from BrinkServiceTool to ebusd .csv file type
sensor_datatype_conversion = {
    'WordSignedValue': "SIR", 
    'WordValue': "UIR",
    'LongValue': "ULR",
    'WordTruncString': "UIR",
    'WordString': "UIR",
}

# Sometimes we know the enum even if the UI retrieved converter would give only conversion to a number
manual_values_sensors_subset = {
    0x18: "0=Clean;1=Dirty", # FilterStatus
}

def multiplier_to_divider(multiplier):
    if multiplier < 1:
        return 1 / multiplier
    elif multiplier > 1:
        return -multiplier
    else:
        return 1

def csv_line_sensor(sensor: sensor_data.Sensor):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    if len(sensor.converter.values) > 0:
        values = sensor.converter.values
        type = sensor.converter.type
    elif int(sensor.id, 16) in manual_values_sensors:
        print(f'Warning: using manual sensor values for {sensor.name}')
        values = manual_values_sensors[int(id, 16)]
        type = 'UIR'
    else:
        values = ""
        type = "SIR"

    return f'r,{sensor.device_lowercase},{sensor.name},{sensor.name},,,4022,{sensor.id},,,{type},{values},{sensor.unit},\n'
 
def csv_line_param_read(circuit, name, id, unit, datatype):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    if int(id, 16) in known_values_params:
        values = known_values_params[int(id, 16)]
        # for known enum we ignore the min/max/step parameters; we only care about the default
        # TODO add the above comment into comment in CSV
        return f'r,{circuit},{name},{name},,,4050,{id},,,{datatype},{values},{unit},,,,IGN:3,,,,Default,,{datatype},{values},{unit},\n'
    else:
        values = ""
        return f'r,{circuit},{name},{name},,,4050,{id},,,{datatype},{values},{unit},,Max,,{datatype},,{unit},,Min,,{datatype},,{unit},,Step,,{datatype},,{unit},,Default,,{datatype},,{unit},\n'
 
def csv_line_param_write(circuit, name, id, unit, datatype):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    if int(id, 16) in known_values_params:
        values = known_values_params[int(id, 16)]
    else:
        values = ""
    return f'w,{circuit},{name},{name},,,4080,{id},,,{datatype},{values},{unit},\n'
 
csv_header = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'

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
        file_str += csv_line_param_read(device_param.name, param.name, param.id, param.unit, datatype_from_sign(param.is_signed))
        if not param.is_read_only:
            file_str += csv_line_param_write(device_param.name, param.name, param.id, param.unit, datatype_from_sign(param.is_signed))
    return file_str

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