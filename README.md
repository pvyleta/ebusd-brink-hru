# ebusd-brink-hru
Collection of Brink HRU configuration files for ebusd

The configuration files were created by parsing the [Brink Service Tool](https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en) decompiled through [JetBrains DotPeak](https://www.jetbrains.com/decompiler/). The decompiled source code is not distributed in this repo for it likely being a violation of the license agreement, though decompiling SW with the intention of interfacing to it can be considered legal. This is also a reason why parsing the code through independent python script was used, rather than re-using portions of the decompiled source code in a new C# binary.

For few parameters, other sources than the decompiled Brink Service Tool was used, such as datasheets, random internet forums etc. This is always noted in the source code, or even in the produced files.

# repo structure
## ebusd-configuration
Contains the config files for individual Brink devices. There are two types of files - sensors and params. Sensors are read only, while params are almost in all instances writable. For params, each message contains five fields: [current, min, max, step_size, default]. This is reflected in the generated .csv files.

Since Brink uses non*standar identification response (0704h message), it is not that straightforward to fabricate the .csv files so that they can be directly consumed by ebusd. Therefore, we just create 'blocks' of CSV data for the given device, which you then need to adjust to match the ebus slave address of your device. Unfortunately, the default slave address of a device is a parameter not foudn in Brink Service Tool. Please, report those numbers, and we can gradually build the files for those devices, that would be directly consumable by ebusd

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
