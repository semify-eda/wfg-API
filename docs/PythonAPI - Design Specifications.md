# Python API Functionalities and Requirements
This API was designed to simplify the SmartWave debugging and verification. It accesses the onboard FPGA's control 
registers, executing erase, read, write, and CRC operations while maintaining the ability to modify control registers 
without affecting the RTL.

The API should follow the WebGUI Communication protocol as outlined here: 
https://github.com/semify-eda/wfg-webgui/blob/main/doc/WebGUI-Arduino-protocol.md 

## Basic functionalities

