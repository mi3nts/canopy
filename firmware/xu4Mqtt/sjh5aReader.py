import time
import sys
import serial
import datetime

# dataFolderReference    = mD.dataFolderReference
# ozonePort              = mD.ozonePort

ozonePort = "/dev/tty.usbserial-AU0645LQ"

baudRate = 9600

def calculate_checksum(data):
    """Calculate the checksum for the response."""
    return sum(data[:-1]) & 0xFF  # Exclude checksum byte from calculation

# def main():
#     ser = serial.Serial(
#         port=ozonePort,
#         baudrate=baudRate,
#         parity=serial.PARITY_NONE,
#         stopbits=serial.STOPBITS_ONE,
#         bytesize=serial.EIGHTBITS,
#         timeout=1,  # Adjust timeout as needed
#     )

#     print(f"Connected to: {ser.portstr}\n")

#     # Send command
#     command = bytes([0x11, 0x01, 0x01, 0xED])
#     ser.write(command)
#     print(f"Sent: {command.hex()}")

#     # Read response
#     time.sleep(1)  # Allow time for response
#     response = ser.read(ser.in_waiting or 8)  # Read available bytes, expecting at least 8 bytes
#     print("R")
#     print(response)
#     if len(response) < 8:
#         print("Incomplete response received.")
#         ser.close()
#         return

#     # Parse response
#     ack = response[0]
#     if ack != 0x06:  # Check if ACK is 0x06
#         print(f"Unexpected ACK byte: {ack}")
#         ser.close()
#         return

#     df1 = response[3]
#     df2 = response[4]
#     st1 = response[5]
#     st2 = response[6]
#     checksum = response[7]

#     # Verify checksum
#     if calculate_checksum(response) != checksum:
#         print("Checksum mismatch! Data may be corrupted.")
#         ser.close()
#         return

#     # Calculate Gas 1 concentration
#     gas_concentration = (df1 * 256 + df2) / 100.0  # Standard calculation
#     print(f"Gas 1 Concentration: {gas_concentration} units")

#     # Optional: Interpret status bytes (st1, st2)
#     print(f"Status Bytes: ST1={st1}, ST2={st2}")

#     ser.close()


# def main():

#     menuSetUp = False

#     ser = serial.Serial(
#     port= ozonePort,\
#     baudrate=baudRate,\
# 	parity  =serial.PARITY_NONE,\
# 	stopbits=serial.STOPBITS_ONE,\
# 	bytesize=serial.EIGHTBITS,\
#     timeout=0)

#     print(" ")
#     print("Connected to: " + ser.portstr)
#     print(" ")
#     line = []
#     ser.write(str.encode('x'))
#     while True:
#         try:
#             command = bytes([0x11, 0x01, 0x01, 0xED])
#             ser.write(command)
#             print(f"Sent: {command.hex()}")
#             time.sleep(.1)
#             for c in ser.read():
#                 line.append(chr(c))
#                 print(c)
#                 if chr(c) == '\n' and (menuSetUp):
#                     dataString = (''.join(line)).replace("\n","").replace("\r","")
#                     print(dataString)
#                     line = []
# #                 # if chr(c) == '\n' and not(menuSetUp):
# #                 #     dataString = ''.join(line)
# #                 #     dataString     = (''.join(line)).replace("\n","").replace("\r","")
                    
# #                 #     print("Entering Menu")
# #                 #     ser.write(str.encode('m'))
# #                 #     time.sleep(2)
# #                 #     print("Setting Frequency to 10 Seconds")
# #                 #     ser.write(str.encode('a'))
# #                 #     time.sleep(2)
# #                 #     ser.write(str.encode('1'))
# #                 #     time.sleep(2)

# #                 #     print("Setting Ozone Units to ppb")
# #                 #     ser.write(str.encode('u'))
# #                 #     time.sleep(2)
# #                 #     ser.write(str.encode('0'))
# #                 #     time.sleep(2)

# #                 #     print("Setting Temperature Units to C")
# #                 #     ser.write(str.encode('c'))
# #                 #     time.sleep(2)
# #                 #     ser.write(str.encode('1'))
# #                 #     time.sleep(2)

# #                 #     print("Setting Pressure Units to mbar")
# #                 #     ser.write(str.encode('o'))
# #                 #     time.sleep(2)
# #                 #     ser.write(str.encode('1'))
# #                 #     time.sleep(2)

# #                 #     print("Exiting Menu")
# #                 #     ser.write(str.encode('x'))
# #                 #     time.sleep(2)
# #                 #     menuSetUp = True
# #                 #     line = []


#         except:
#             print("Incomplete read. Something may be wrong with {0}".format(ozonePort[0]))
#             line = []




def calculate_checksum(data):
    """Calculate the checksum for the response."""
    return sum(data[:-1]) & 0xFF  # Exclude checksum byte from calculation

def main():
    ser = serial.Serial(
        port=ozonePort,
        baudrate=baudRate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1,  # Adjust timeout as needed
    )

    print(f"Connected to: {ser.portstr}\n")

    # Send command
    command = bytes([0x11, 0x01, 0x01, 0xED])
    ser.write(command)
    print(f"Sent: {command.hex()}")

    # Read response
    time.sleep(1)  # Allow time for response
    response = ser.read(ser.in_waiting or 8)  # Read available bytes, expecting at least 8 bytes
    print(response)

    if len(response) < 8:
        print("Incomplete response received.")
        ser.close()
        return

    # Parse response
    ack = response[0]
    if ack != 0x06:  # Check if ACK is 0x06
        print(f"Unexpected ACK byte: {ack}")
        ser.close()
        return

    df1 = response[3]
    df2 = response[4]
    st1 = response[5]
    st2 = response[6]
    checksum = response[7]

    # Verify checksum
    if calculate_checksum(response) != checksum:
        print("Checksum mismatch! Data may be corrupted.")
        ser.close()
        return

    # Calculate Gas 1 concentration
    gas_concentration = (df1 * 256 + df2) / 100.0  # Standard calculation
    print(f"Gas 1 Concentration: {gas_concentration} units")

    # Optional: Interpret status bytes (st1, st2)
    print(f"Status Bytes: ST1={st1}, ST2={st2}")

    ser.close()





if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print("Monitoring Methane Sensor on port: {0}".format(ozonePort)+ " with baudrate " + str(baudRate))
    main()