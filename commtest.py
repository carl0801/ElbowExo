import serial
import struct
import time
class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s
        self.start_byte = 0xff
        self.end_byte = 0x0a
        self.ack_byte = 0x06
        self.chk_byte = 0x0202
        self.ack_pack = struct.pack('<BBHB', self.start_byte, self.ack_byte, self.chk_byte, self.end_byte)
        self.data_request_pack = struct.pack('<BBHB', self.start_byte, 0x02, self.chk_byte, self.end_byte)
        self.pos_offset = 5000
        self.ack = False
    
    def readline(self):
        while True:
            # Check for patterns in the buffer
            data_start = self.buf.find(b"\xff\xff")
            ack_start = self.buf.find(b"\xff\x06")
            newline_pos = self.buf.find(b"\n")

            # Handle data packet
            if data_start != -1 and len(self.buf) >= data_start + 10:
                if self.buf[data_start + 9:data_start + 10] == b"\n":
                    # Valid data packet
                    packet = self.buf[data_start:data_start + 10]
                    del self.buf[:data_start + 10]  # Remove processed packet
                    packet = self._process_packet(packet, 0)
                    if packet is not None:
                        return packet
                    else:
                        return None

            # Handle ACK packet
            if ack_start != -1 and len(self.buf) >= ack_start + 5:
                if self.buf[ack_start + 4:ack_start + 5] == b"\n":
                    # Valid ACK packet
                    packet = self.buf[ack_start:ack_start + 5]
                    del self.buf[:ack_start + 5]  # Remove processed packet
                    packet = self._process_packet(packet, 1)
                    if packet is not None:
                        return "ACK"
                    else:
                        return None

            # Handle string (if no potential packet found or enough bytes aren't present)
            if newline_pos != -1:
                if (data_start == -1 or newline_pos < data_start) and \
                   (ack_start == -1 or newline_pos < ack_start):
                    # Valid string (not part of a data or ACK packet)
                    string = self.buf[:newline_pos + 1].decode("utf-8")
                    del self.buf[:newline_pos + 1]  # Remove processed string
                    return string

            # If no newline or full packet is found, read more data
            self._read_more()

    def _read_more(self):
        """Read more data from the serial port."""
        i = max(1, min(200, self.s.in_waiting))
        data = self.s.read(i)
        self.buf.extend(data)
        
    def _verify_checksum(self, packet):
        """Helper method to verify 2-byte checksum of packet."""
        value1 = packet[3]
        value2, value3 = struct.unpack('<hh', packet[4:8])
        
        checksum = value1
        checksum ^= (value2 & 0xFF)       # XOR lower byte of value2
        checksum ^= ((value2 >> 8) & 0xFF) # XOR upper byte of value2
        checksum ^= (value3 & 0xFF)       # XOR lower byte of value3
        checksum ^= ((value3 >> 8) & 0xFF) # XOR upper byte of value3
        
        if checksum == struct.unpack('<H', packet[8:10]):
            return True
        return False
    
    def _process_packet(self, packet, t):
        """Helper method to process a packet based on its type."""
        match t:
            case 0:
                # calculate parity to check if packet is valid
                if True:#self._verify_checksum(packet):
                    self.r = packet
                    self.last_checksum = struct.unpack('<H', packet[8:10])
                    self.buf = self.buf[10:]
                    return packet
                else:
                    return None
            case 1:
                if True:#packet[2:4] == self.last_checksum.to_bytes(2, byteorder='little'):
                    return "ACK"
                else:
                    return None

    
    # Function to create a packet with the 3 validity bits, 5 boolean values, and velocity(int16_t)
    def send_packet(self, mot_en, mot_stl, enc_rst, velocity):
        
        bool_byte = 0x00000010
        bool_byte |= mot_en << 4
        bool_byte |= mot_stl << 3
        bool_byte |= enc_rst << 2
        # Create the byte packet
        packet = struct.pack('<BBhB', self.start_byte, bool_byte, velocity, self.end_byte)
        if self.s and self.s.is_open:
            self.s.write(packet)

    def send_ack(self):
        if self.s and self.s.is_open:
            self.s.write(self.ack_pack)

    def read_data(self):
        data = self.readline()
        # if second byte is also a start byte, it is a data packet
        if data is not None:
            try:
                if data[1] == self.start_byte:
                    self.send_ack()
                    return self.unpack_data(data)
                elif data[1] == self.ack_byte:
                    self.ack = True
                else:
                    print("Invalid data packet received: ", data)
            except IndexError:
                print("Invalid data packet received: ", data)
        else:
            return None

    def unpack_data(self, data):
        
        try:
            # Unpack the data
            start, type_byte, bool_byte, velocity, position, checksum, end = struct.unpack('<BBBhhhB', data)
            # Extract the boolean values
            mot_en = (bool_byte >> 4) & 0x01
            mot_stl = (bool_byte >> 3) & 0x01
            enc_rst = (bool_byte >> 2) & 0x01
            return mot_en, mot_stl, enc_rst, velocity, position-self.pos_offset, checksum
        except struct.error:
            print("Error unpacking data. Length of data: ", len(data), "Data: ", data)
            
    def send_data_request(self):
        if self.s and self.s.is_open:
            self.s.write(self.data_request_pack)
            
    def reset_encoder(self):
        self.send_packet(0, 0, 1, 0)
        if self.s and self.s.is_open:
            #print("Encoder reset.")
            pass
            
            
ser = serial.Serial('COM9', 115200)
if ser.isOpen():
    print("Serial port is open.")

rl = ReadLine(ser)

sample_size = 1000
working = True
cycles = 0
last_time = time.time()
last_time2 = time.time()
delta_time = []
while working:
    if time.time() - last_time > 5:
        rl.reset_encoder()
        last_time = time.time()
    data = rl.read_data()
    if data != None:
        rl.ack = True
        #print(data)
        #data = rl.read_data()
        mot_en, mot_stl, enc_rst, velocity, position, checksum = data
        delta_time.append(time.time() - last_time2)
        # print data in a zero-padded string with \r at the end
        print(f"{mot_en} | {mot_stl} | {enc_rst} | {velocity:05d} | {position:05d}", end="\r")
        cycles += 1
        if cycles == sample_size:
            working = False
        last_time2 = time.time()

print("\nAverage time per cycle: ", sum(delta_time)/len(delta_time))
print(f"Max time per cycle: {max(delta_time)}")
print(f"Min time per cycle: {min(delta_time)}")

        
    
        