import serial
import time
# Serial port configuration
methanePort = "/dev/tty.usbserial-0001"  # Replace with your port
baudRate = 38400

def main():
    """
    Main function to read data from the methane sensor via the serial port
    and display both ASCII and HEX values, keeping only the last two ASCII characters.
    """
    try:
        # Serial connection setup
        ser = serial.Serial(
            port=methanePort,
            baudrate=baudRate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
            timeout=0,
        )
        time.sleep(1)
        print("\nConnected to: " + ser.portstr + "\n")
        time.sleep(1)
        print("Entering Configuration Mode")
        configMode, response   = send_command("C",ser)
        print("Read Back Settings Mode")
        readSettings, response = send_command("I",ser)

        lineASCII = []


    #     while True:
    #         try:
    #             # Read bytes from the serial buffer
    #             for byte in ser.read():
    #                 ascii_char = chr(byte)  # if 32 <= byte <= 126 else "."  # Handle printable and non-printable characters
    #                 lineASCII.append(ascii_char)

    #                 data = ''.join(lineASCII)
    #                 lines = data.split("\n\r")
    #                 lines = [line for line in lines if line.strip()]

    #                 print(lines)
    #                 if lines and lines[-1] == "0000005d":
    #                     if lines[0] == "0000005b":
    #                         print(lines)
    #                         methanePPM        = int(lines[1], 16)
    #                         faultCode         = lines[2]
    #                         sensorTemperature = (int(lines[3], 16)/10)- 273.15
    #                         CRC               = int(lines[4], 16)
    #                         CRC1sComp         = int(lines[5], 16)                  
    #                         print("Methane Concentration = " + str(methanePPM) + " ppm")
    #                         print("Fault Code            = " + str(faultCode))
    #                         print("Sensor Temperature    = " + str(sensorTemperature) + " C")
    #                         print("CRC                   = " + str(CRC))
    #                         print("CRC1sComp             = " + str(CRC1sComp))
    #                         # send_command("A",ser)
    #                     lineASCII = []
    #                     lines     = []

    #                 # else:
    #                 #     print(f"Last line is not '0000005d'. Found: {lines[-1] if lines else 'None'}")


            
    #         except Exception as e:
    #             print(f"Incomplete read. Error: {e}")
    #             break  # Exit the loop if an error occurs

    except serial.SerialException as e:
        print(f"Failed to connect to {methanePort}. Error: {e}")


def send_command(command,ser):
    if not command.isalpha() or len(command) != 1:
        print("Invalid command. Use a single uppercase letter.")
        return
    # Format the command structure and encode it
    full_command = f"[{command.upper()}]"
    ser.write(full_command.encode())
    print(f"Sent command: {full_command}")
    time.sleep(.1)
    response = ser.read(500).decode(errors="ignore")
    # print(response)
    response = response.strip()
    print(f"Response: {response.strip()}")
    time.sleep(.1)
    if response.endswith("5b414b5d"):
        print("Command Accepted")
        return True,response
    else:
        return False,response
        



    # Read response if available
    # response = ser.read(100).decode(errors="ignore")
    # print(f"Response: {response.strip()}")

if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print(f"Monitoring Methane Sensor on port: {methanePort} with baudrate {baudRate}")
    main()