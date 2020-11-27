# imports

import socket
import random
import sys
import time

# data

UDP_IP = "127.0.0.1"
UDP_PORT = 1235
OTHER_PORT = 6363
RANDOM_DROP_PROB = 0.1
MAX_PACKETS = 100
DEBUG_MODE = False

# input cmd line
args = len(sys.argv)
i = 1
while(i < args):
	if(sys.argv[i] == "-d"):
		DEBUG_MODE = True
	if(sys.argv[i] == "-p"):
		i += 1
		UDP_PORT = int(sys.argv[i])
	if(sys.argv[i] == "-n"):
		i += 1
		MAX_PACKETS = int(sys.argv[i])
	if(sys.argv[i] == "-e"):
		i += 1
		RANDOM_DROP_PROB = int(sys.argv[i])
	i += 1


# SR Reciever


sock = socket.socket(socket.AF_INET, # Internet
					 socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

sock_ack = socket.socket(socket.AF_INET, # Internet
					 socket.SOCK_DGRAM) # UDP

rcv_buff = [i for i in range(MAX_PACKETS)]
retrans = 0
debug = [[] for i in range(MAX_PACKETS)]
start_time = time.time()

while (True):
	data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
	if(data != None):
		retrans += 1
		word = data.decode('utf-8')
		word = word[:word.find('~')]
		val = int(word)
		#print("recieved : "+word)
		if(random.random() > RANDOM_DROP_PROB):
			try:
				rcv_buff.remove(val)
			except:
				continue
			debug[val].append(time.time() - start_time)
			retrans = 0
			#print("ack_recieved : "+word)
			bt = bytes(word,'utf-8')
			sock_ack.sendto(bt,(UDP_IP,OTHER_PORT))
	
	if(len(rcv_buff) == 0 or retrans > 8):
		sock_ack.sendto(b'-1',(UDP_IP,OTHER_PORT))
		break
		
if(DEBUG_MODE):
	j = 0
	for pac in debug:
		print(str(j) + " : ",end="")
		print(pac)
		j += 1
print("reciever terminated")