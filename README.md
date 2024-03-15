# ebusd-brink-hru
Collection of Brink HRU configuration files for ebusd

The configuration files were created by parsing the [Brink Service Tool](https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en) decompiled through [JetBrains DotPeak](https://www.jetbrains.com/decompiler/). The decompiled source code is not distributed in this repo for it likely being a violation of the license agreement, though decompiling SW with the intention of interfacing to it can be considered legal. This is also a reason why parsing the code through independent python script was used, rather than re-using portions of the decompiled source code in a new C# binary.

For few parameters, other sources than the decompiled Brink Service Tool was used, such as datasheets, random internet forums etc. This is always noted in the source code, or even in the produced files.

# Supported devices

Currently, the ebusd-configuration for these heat recovery units is present:

 - Brink CWLF250
 - Brink CWLF350
 - Brink CWLTower300
 - Brink ConstantRPM400
 - Brink DecentralAir70
 - Brink Elan10
 - Brink Elan4
 - Brink Renovent Excellent180
 - Brink Renovent Excellent300
 - Brink Renovent Excellent400
 - Brink Renovent Excellent450
 - Brink Flair200
 - Brink Flair225
 - Brink Flair300
 - Brink Flair325
 - Brink Flair400
 - Brink Flair450
 - Brink Flair600
 - Brink MultiRoomCtrlT01
 - Brink Nather300
 - Brink RenoventElan300
 - Brink Renovent Sky150
 - Brink Renovent Sky200
 - Brink Renovent Sky300
 - Brink ValveT01
 - Viessmann Vitovent200W
 - Viessmann Vitovent300C
 - Viessmann Vitovent300W300
 - Viessmann Vitovent300W400
 - Viessmann Vitovent300WH32SA225
 - Viessmann Vitovent300WH32SA600
 - Viessmann Vitovent300WH32SC400
 - Viessmann Vitovent300WH32SC325

 Note, that Brink devices are re-branded as Viessmann, Wolf, VisionAIR, Ubbink and maybe others, os these configuration files are (mostly) applicable for those as well.

# repo structure
## ebusd-configuration
Contains the config files for individual Brink devices. There are two types of files - sensors and params. Sensors are read only, while params are almost in all instances writable. For params, each message contains five fields: [current, min, max, step_size, default]. This is reflected in the generated .csv files.

The naming format is [device].[first_sw_version].[last_sw_version].[sensors|params.basic|params.plus].csv, where the range first-last SW versions is the range of versions this file is applicable for, sensors is for sensors, params.plus are params for plus version of device and params.basic is for basic version of the device. Note, that not all devices have basic/plus version, but for simplicity we write out bot for every device - sometimes those files are just identical.

Since Brink uses non-standard identification response (0704h message), it is not that straightforward to fabricate the .csv files so that they can be directly consumed by ebusd. Therefore, we just create 'blocks' of CSV data for the given device, which you then need to adjust to match the ebus slave address of your device. Unfortunately, the default slave address of a device is a parameter not foudn in Brink Service Tool. Please, report those numbers, and we can gradually build the files for those devices, that would be directly consumable by ebusd.

## src
Contains the python scripts used to parse the decompiled Brink Service Tool. They are not exactly pretty, but they do the jobs and they contain reasonable number of sanity checks. The scripts are expected to be run from the root repo directory, i.e. `python .\src\main.py`

## BCSServiceTool
This folder is expected to be filled in with the decompiled binary.

The version of tool used and tested with the parsing scripts is 'S1_04_11_0002'

## dump
Contains dump of the parsed data in fairly re-usable JSON and CSV formats. if you plan to integrate Brink HRUs in other software than ebusd, this is the place to go.

# TODO
- add German translation based on the translations present in Brink Service Tool
- structure config files better with using !include instructions and conditions
- find out slave IDs for more Brink HRUs
