import serial
import serial.tools.list_ports





portlist = list(serial.tools.list_ports.comports())



i = 0
valid = 0
for port in portlist:
  #print(port)
  #print("[{}] {} {} {}".format(i, port[0], port[1], port[2]))

  if(port[2].startswith("USB VID:PID=2341:804F")): #Arduino MKR zero
    print("matched Arduino MKR zero")
    valid = 1
    break

  i+=1


if valid:
  with serial.Serial(portlist[i][0], 9600, timeout=1) as smartWave:
    smartWave.write('test'.encode('ascii'))
