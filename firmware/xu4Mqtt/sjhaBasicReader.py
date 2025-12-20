import serial

# Serial port configuration
methanePort = "/dev/tty.usbserial-0001"  # Replace with your port
baudRate = 38400

def main():
    """
    Main function to read data from the methane sensor via the serial port
    and display both ASCII and HEX values.
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
        
        print("\nConnected to: " + ser.portstr + "\n")
        
        while True:
            try:
                # Read bytes from the serial buffer
                for byte in ser.read():
                    hex_value = hex(byte)  # Convert byte to hexadecimal
                    # Convert byte to ASCII, handle non-printable characters
                    if 32 <= byte <= 126:
                        ascii_char = chr(byte)  # Printable ASCII
                    else:
                        ascii_char = "."  # Placeholder for non-printable
                    
                    print(f"ASCII: {ascii_char} | HEX: {hex_value}")
            except Exception as e:
                print(f"Incomplete read. Error: {e}")
                break  # Exit the loop if an error occurs

    except serial.SerialException as e:
        print(f"Failed to connect to {methanePort}. Error: {e}")

if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print(f"Monitoring Methane Sensor on port: {methanePort} with baudrate {baudRate}")
    main()