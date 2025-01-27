import serial
import time

# Set up ozone port and baud rate
ozonePort = "/dev/tty.usbserial-AU0645LQ"
baudRate = 38400

def send_uart_command(command_char):
    try:
        # Set up the serial connection
        ser = serial.Serial(
            port=ozonePort,
            baudrate=baudRate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        
        print(f"Connected to: {ser.portstr}")
        
        # Prepend '[' (0x5B) and append ']' (0x5D) to the command character
        command = bytes([0x5B, ord(command_char), 0x5D])  # [command_char] in hex format
        
        ser.write(command)  # Write the byte sequence to UART
        
        print(f"Sent Command: {command}")
        
        time.sleep(1)  # Wait for 1 second before checking response
        
        # Read response: Read all available bytes in the buffer
        response_bytes = ser.read(ser.in_waiting)
        
        if response_bytes:
            # Convert the response bytes to an ASCII string
            response_ascii = response_bytes.decode('ascii')
            print(f"Response (ASCII): {response_ascii}")
        else:
            print("No response received.")
        
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if ser.is_open:
            ser.close()  # Close the serial port

if __name__ == "__main__":
    send_uart_command('A')  # Send the [A] command to enter NORMAL mode
