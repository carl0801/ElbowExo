import time
import struct
import serial
import libraries.com as com
import random
import string

# simulated serial self.buffer

# create byte array with 2 bytes
data_packet = bytearray()
start = bytearray(1)
start[0] = 0xff
end = bytearray(1)
end[0] = 0x0a
info = bytearray(1)
info[0] = 0x02
byte = bytearray(1)
byte[0] = 0x42
ack = bytearray(1)
ack[0] = 0x06
data_packet.extend(start)
data_packet.extend(start)
for i in range(10):
    data_packet.extend(byte)
data_packet.extend(end)

ack_packet = bytearray()
ack_packet.extend(start)
ack_packet.extend(ack)
ack_packet.extend(end)

    # def readline(self):
    #     i = self.buf.find(b"\n")
    #     if i >= 0:
    #         if self.buf[:i+1] == b"\xff\x06\n": # if first 3 bytes are an ack packet
    #             r = self.buf[:i+1]
    #             self.buf = self.buf[i+1:]
    #             #return r
    #             return "ACK"
    #        
    #         if self.buf[:2] == b"\xff\xff" and self.buf[12:13] == b"\n": # if data packet
    #             # self.buf[12] is an int, self.buf[12:13] is a byte. python is fun.
    #             # read 13 bytes for data packet and return
    #             r = self.buf[:13]
    #             self.buf = self.buf[13:]
    #             #return r 
    #             return "DATA"
    #        
    #         else:
    #             # if it isn't ack or data, it must be a string. return it.
    #             r = self.buf[:i+1]
    #             self.buf = self.buf[i+1:]
    #             return r
    #
    #     while True:
    #         i = max(1, min(256, len(self.ser)))
    #         data = self.ser[:i+1]
    #         # simulate serial self.buffer by removing bytes from self.ser
    #         self.ser = self.ser[i+1:]
    #         i = data.find(b"\n")
    #         if i >= 0:
    #             if self.data[:i+1] == b"\xff\x06\n": # if first 3 bytes are an ack packet
    #                 r = self.buf + data[:i+1]
    #                 self.buf[0:] = data[i+1:]
    #                 return r
    #             if self.buf[:2] == b"\xff\xff" and self.buf[12:13] == b'\n':
    #                 # read 13 bytes for data packet and return
    #                 r = self.buf[:13]
    #                 self.buf = self.buf[13:]
    #                 return r 
    #             else:
    #                 # if it isn't ack or data, it must be a string. return it.
    #                 r = self.buf[:i+1]
    #                 self.buf = self.buf[i+1:]
    #                 return r
    #         else:
    #             self.buf.extend(data)
    #         self.add_serial()

# class ReadLine:
#     def __init__(self, s):
#         self.buf = bytearray()
#         self.s = s

#     def readline(self):
#         i = self.buf.find(b"\n")
#         if i >= 0:
#             r = self.buf[:i+1]
#             self.buf = self.buf[i+1:]
#             return r
#         while True:
#             i = max(1, min(2048, self.s.in_waiting))
#             data = self.s.read(i)
#             i = data.find(b"\n")
#             if i >= 0:
#                 r = self.buf + data[:i+1]
#                 self.buf[0:] = data[i+1:]
#                 return r
#             else:
#                 self.buf.extend(data)

# ser = serial.Serial('COM7', 9600)
# rl = ReadLine(ser)

# while True:

#     print(rl.readline())

class read_line_sim:
    def __init__(self):
        self.send_amount = 50
        
        self.buf = bytearray()
        self.ser = bytearray()
        #self.ser.extend(ack_packet)
        self.send_packet = 1#random.choice([0,1,2])
        self.send = True
        self.cur_byte = 0
        self.data_len = 10
        self.ack_len = 5
        self.ack_pack = bytearray()
        self.last_checksum = 0
        self.count = 0
        self.packet_pos = []
        self.packet_vel = []
        self.vels = []
        self.pos = []
        self.fails = []
        self.packets = []
        self.raw_packets = []
        self.acks = []
        self.chcksums = []
        self.strings = []
        self.stringbytes = []
        self.parsed_strings = []
        self.stringfails = []
        self.random_string = ''
        self.random_string_bytes = 0
        self.string_len = 0
        self.raws = []
        self.full_stream = bytearray()
        #self.full_stream.extend(ack_packet)
        self.randposbytes = 0
        self.randpos = 0
        self.randvelbytes = 0
        self.randvel = 0
        self.packet = 0
        self.ground_truth = []
        self.next_len = 0
        self.generate_next()
        
    # function which generates a random 64bit integer and outputs it as a byte array and as a value
    def random_bytes(self, len=2):
        random_pos_neg = random.getrandbits(1)
        random_int = random.getrandbits(15)
        random_bytes = random_int.to_bytes(len, byteorder='little', signed=True)
        return random_bytes, random_int

    def make_ack_packet(self):
        ack_packet = bytearray(5)
        ack_packet.extend(start)
        ack_packet.extend(ack)
        ack_packet.extend(self.last_checksum.to_bytes(2, byteorder='little'))
        ack_packet.extend(end)
        return ack_packet
    
    # def calculate_checksum(self, packet):
    #     value1 = packet[3]
    #     value2 = packet[4:6]
    #     value3 = packet[6:8]
        
    #     if type(value1) != bytearray:
    #         value1 = value1.to_bytes(1, byteorder='little')
    #     if type(value2) != bytearray:
    #         value2 = value2.to_bytes(2, byteorder='little')
    #     if type(value3) != bytearray:
    #         value3 = value3.to_bytes(2, byteorder='little')
    #     checksum = 0x00 ^ (value1 & 0xFF) # XOR lower byte of value1
    #     checksum ^= (value2 & 0xFF)       # XOR lower byte of value2
    #     checksum ^= ((value2 >> 8) & 0xFF) # XOR upper byte of value2
    #     checksum ^= (value3 & 0xFF)       # XOR lower byte of value3
    #     checksum ^= ((value3 >> 8) & 0xFF) # XOR upper byte of value3
    #     return checksum
    
    def calculate_checksum(self, packet):
        value1 = packet[3]
        value2 = packet[4:6]
        value3 = packet[6:8]

        if type(value1) != int:
            value1 = int.from_bytes(value1.to_bytes(1, byteorder='little'), byteorder='little')
        if type(value2) != int:
            value2 = int.from_bytes(value2, byteorder='little')
        if type(value3) != int:
            value3 = int.from_bytes(value3, byteorder='little')

        checksum = 0x00 ^ (value1 & 0xFF)  # XOR lower byte of value1
        checksum ^= (value2 & 0xFF)        # XOR lower byte of value2
        checksum ^= ((value2 >> 8) & 0xFF) # XOR upper byte of value2
        checksum ^= (value3 & 0xFF)        # XOR lower byte of value3
        checksum ^= ((value3 >> 8) & 0xFF) # XOR upper byte of value3

        return checksum
    
    def generate_next(self):
        self.ground_truth.append(self.send_packet)
        match self.send_packet:
            case 0:
                self.randposbytes, self.randpos = self.random_bytes()
                self.randvelbytes, self.randvel = self.random_bytes()
                self.pos.append(self.randpos)
                self.vels.append(self.randvel)
                self.packet = self.make_packet(self.randvelbytes, self.randposbytes)
                self.checksum = self.calculate_checksum(self.packet)
                self.packet[8:10] = self.checksum.to_bytes(2, byteorder='little')
                self.next_len = self.data_len
            case 1:
                self.ack_pack = self.make_ack_packet()
                self.acks.append(self.ack_pack)
                self.next_len = self.ack_len
            case 2:
                self.random_string = ''.join(random.choices(string.printable, k=random.randint(1, 20)))
                self.random_string_bytes = self.random_string.encode()
                self.string_len = len(self.random_string)
                self.next_len = self.string_len
                self.strings.append(self.random_string)
                self.stringbytes.append(self.random_string_bytes)
    
    def make_packet(self, velarray, posarray):
        # create byte array with 2 bytes
        packet = bytearray()
        packet.extend(start)
        packet.extend(start)
        packet.extend(info)
        for i in range(2):
            packet.extend(velarray[i:i+1])
        for i in range(2):
            packet.extend(posarray[i:i+1])
        packet.extend(end)
        packet.extend(end)
        self.packets.append(packet)
        return packet

    def add_serial(self):
        # simulate extending serial self.buffer by [0:k] bytes at a time
        bytes_to_add = random.randint(0, 10)
        zero_risk = random.randint(0, 100)
        if zero_risk < 5:
            bytes_to_add = 0
        for i in range(bytes_to_add):
            match self.send_packet:
                case 0:
                    rl.full_stream.extend(self.packet[self.cur_byte:self.cur_byte+1])
                    rl.ser.extend(self.packet[self.cur_byte:self.cur_byte+1])
                    self.cur_byte += 1
                case 1:
                    rl.ser.extend(ack_packet[self.cur_byte:self.cur_byte+1])
                    rl.full_stream.extend(ack_packet[self.cur_byte:self.cur_byte+1])
                    self.cur_byte += 1
                case 2:
                    rl.ser.extend(self.random_string_bytes[self.cur_byte:self.cur_byte+1])
                    rl.full_stream.extend(self.random_string_bytes[self.cur_byte:self.cur_byte+1])
                    self.cur_byte += 1
            if self.cur_byte == self.data_len:
                self.count += 1
                if self.count == self.send_amount:
                    self.send = False
                    break
                else:
                    risk = random.randint(0, 100)
                    response = random.randint(0, 100)
                    packetloss = 0 if risk < 80 else 1
                    match self.send_packet:
                        case 0:
                            if packetloss == 1:
                                self.send_packet = random.choice([0,1,2])
                                self.cur_byte = 0
                                self.generate_next()
                            else:
                                self.send_packet = random.choice([1,2])
                                self.cur_byte = 0
                                self.generate_next()
                        case 1:
                            if packetloss == 1:
                                self.send_packet = 2 if response < 60 else 1
                                self.cur_byte = 0
                                self.generate_next()
                            else:
                                self.send_packet = 0 if response < 80 else 2
                                self.cur_byte = 0
                                self.generate_next()
                        case 2:
                            self.send_packet = random.choice([0,1,2])
                            self.cur_byte = 0
                            self.generate_next()
                break
            

    
    def readline(self):
        # Check if a newline character exists in the current buffer
        i = self.buf.find(b"\n")
        if i >= 0:
            # Handle potential packets
            pack = self._process_packet(i)
            if pack is not None:
                return pack

        # If no newline, read from serial until a newline is found
        while True:
            # Determine how many bytes to read from serial
            i = max(1, min(5, len(self.ser)))
            # simulate reading serial
            data = self.ser[:i]
            self.ser = self.ser[i:]
            
            self.buf.extend(data)  # Add new data to buffer

            # Check if newline exists in the updated buffer
            i = self.buf.find(b"\n")
            if i >= 0:
                # Process the complete line found
                pack = self._process_packet(i)
                if pack is not None:
                    return pack
            self.add_serial()
    
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
    
    def _process_packet(self, i):
        """Helper method to process a packet based on its type."""
        # Check if it's a potential data packet (starts with b"\xff\xff")
        if len(self.buf) >= 2:
            if self.buf[:2] == b"\xff\xff":
                # If the buffer is too short for a complete data packet, wait for more data
                if len(self.buf) < 10:
                    return None  # Signal that more data is needed

                # Check if the 13th byte is '\n' to confirm it's a valid data packet
                if self.buf[9:10] == b"\n":
                    packet = self.buf[:10]  # Extract the 10-byte data packet
                    # calculate parity to check if packet is valid
                    if self._verify_checksum(packet):
                        self.r = packet
                        self.last_checksum = struct.unpack('<H', packet[8:10])
                        self.buf = self.buf[10:]
            # If the buffer starts with b"\xff\x06\n", it's an ACK packet
            if self.buf[:2] == b"\xff\x06":
                if self.buf[4:5] == b"\n" and self.buf[2:4] == self.last_checksum.to_bytes(2, byteorder='little'):
                    self.buf = self.buf[5:]
                    return "ACK"

        # If it's neither a valid data packet nor an ACK, treat it as a string
        r = self.buf[:i+1]
        self.buf = self.buf[i+1:]  # Remove the string from the buffer
        return r

rl = read_line_sim()

print("Start")
counter = -1
offset = 0
ackcount = 0
while rl.send:
    counter += 1
    data = rl.readline()
    offset = len(rl.ground_truth) - counter
    if data == "ACK":
        ackcount += 1
        rl.raws.append([counter, "OK", data, "A"])
    elif len(data) == 13 and data[0:2] == b"\xff\xff" and data[12:13] == b"\n":
        packetstruct = struct.unpack('<BBhqB', data)
        rl.packet_vel.append(packetstruct[2])
        rl.packet_pos.append(packetstruct[3])
        rl.raw_packets.append(data)
        rl.raws.append([counter, "OK", data, "D"])
        if rl.ground_truth[-1] == 1:
            if (packetstruct[2] == rl.vels[-1] and packetstruct[3] == rl.pos[-1]):# and (packetstruct[2] != rl.vels[-2] or packetstruct[3] != rl.pos[-2]):
                pass
        else:
            print(f"packet fail: {counter} - vel: {packetstruct[2]} - pos: {packetstruct[3]} - rl.vels[-1]:{rl.vels[-1]} - rl.vels[-2]: {rl.vels[-2]} - rl.pos[-1]: {rl.pos[-1]} - rl.pos[-2]: {rl.pos[-2]}")
            rl.fails.append([counter, data, rl.vels[-1], packetstruct[2], rl.pos[-1], packetstruct[3]])
            rl.raws[-1][1] = "ERR"
    else:
        rl.parsed_strings.append(data)
        rl.raw_packets.append(data)
        rl.raws.append([counter, "OK", data, "S"])
        if rl.ground_truth[-1] == 2:
            if data != rl.stringbytes[-1]:
                pass
        else:
            #print(f"String fail {counter}: {data}   |   {rl.stringbytes[-1]}    |   {rl.random_string}")
            try:
                rl.stringfails.append([counter, data, rl.stringbytes[-1], rl.strings[-1]])
            except:    
                rl.stringfails.append([counter, data, 0, 0])
            rl.raws[-1][1] = "ERR"

gt_type = ["DATA", "ACK", "STRING"]

print()
print("Done!")
print()
print(f"ACKs: {ackcount}")
print(f"Data packets: {len(rl.packet_pos)}")
print(f"Strings: {len(rl.parsed_strings)}")
print()
print(f"Fails: {len(rl.fails)}")
for count, i in enumerate(rl.fails):
    print(f"{count} - {i[1]} - {i[2]} - {i[3]} - {i[4]} - {i[0]}")
print()
print("String fails: ", len(rl.stringfails))
overview = 2
for i in rl.stringfails:
    print()
    if i[0] - overview >= 0:
        for j in range(1, overview+1):
            n = i[0]-1-overview + j
            if n >= 0:
                print(f"{rl.raws[n][1]}:{n} - {gt_type[rl.ground_truth[n]]} - {rl.raws[n]} ")
    else:
        for j in range(1, overview+1):
            n = i[0]-1-overview+1+j
            print(f"{rl.raws[n][1]}:{n} - {gt_type[rl.ground_truth[n]]} - {rl.raws[n]} ")
        #print("can't print previous packets")
    print(f"ERR: {i[0]} - {gt_type[rl.ground_truth[i[0]]]} - {i[1]}   |   {i[2]}   |   {i[3]} #")
    if  i[0] + overview <= len(rl.raw_packets):
        for j in range(1,overview+1):
            n = i[0]+j
            
            print(f"{rl.raws[n][1]}:{n} - {gt_type[rl.ground_truth[n]]} - {rl.raws[n]} ")
    else:
        for j in range(1, len(rl.raw_packets) - i[0]):
            n = i[0]+j
            print(f"{rl.raws[n][1]}:{n} - {gt_type[rl.ground_truth[n]]} - {rl.raws[n]} ")


# print bytes from full_stream surrounding the first element in stringfails
print()
print("First string fail:")
print(rl.full_stream[:rl.stringfails[0][0]])

print(f"len generated data: {len(rl.ground_truth)}   |   len received data: {len(rl.raws)}    |     diff: {len(rl.ground_truth) - len(rl.raws)}")
