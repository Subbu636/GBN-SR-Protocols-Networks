# imports

import socket
import sys
import os
import math
import time
import threading

# cmd line parameters
DEBUG_MODE = False
R_ADDRESS = "127.0.0.1"
R_PORT_NUMBER = 1235
OTHER_PORT = 6363
PACKET_LENGTH = 32
PACKET_GEN_RATE = 1000
MAX_PACKETS = 100
WINDOW_SIZE = 3
MAX_BUFFER_SIZE = 10

# getting input
args = len(sys.argv)
i = 1
while(i < args):
	if(sys.argv[i] == "-d"):
		DEBUG_MODE = True
	if(sys.argv[i] == "-s"):
		i += 1
		R_ADDRESS = int(sys.argv[i])
	if(sys.argv[i] == "-p"):
		i += 1
		R_PORT_NUMBER = int(sys.argv[i])
	if(sys.argv[i] == "-l"):
		i += 1
		PACKET_LENGTH = int(sys.argv[i])
	if(sys.argv[i] == "-r"):
		i += 1
		PACKET_GEN_RATE = int(sys.argv[i])
	if(sys.argv[i] == "-n"):
		i += 1
		MAX_PACKETS = int(sys.argv[i])
	if(sys.argv[i] == "-w"):
		i += 1
		WINDOW_SIZE = int(sys.argv[i])
	if(sys.argv[i] == "-b"):
		i += 1
		MAX_BUFFER_SIZE = int(sys.argv[i])
	i += 1

# packet generator

def gen_packs():
	
	period = 1/PACKET_GEN_RATE
	start_time = time.time()
	global create_id
	global buffer
	global debug
	
	while (True):
		if(len(buffer) < MAX_BUFFER_SIZE):
			st = str(create_id)+"~" + "x"*PACKET_LENGTH
			# lock.acquire()
			buffer.append(bytes(st,'utf-8'))
			try:
				debug[create_id].append(time.time() - start_time)
			except:
				k=0
			# lock.release()
			#print("created : "+str(create_id))
			create_id += 1
			# print(time.time() - start_time)
			time.sleep(period)
			
		if(retrans > 8 or succ_send >= MAX_PACKETS):
			break

# packet transmitter

def send_packs():
	
	global un_acks
	global sent_count
	global timers
	
	while (True):
		lock.acquire()
		if(un_acks < WINDOW_SIZE and len(buffer) > un_acks):
			sock.sendto(buffer[un_acks], (R_ADDRESS, R_PORT_NUMBER))
			sent_count += 1
			word = buffer[un_acks].decode('utf-8')
			un_acks += 1
			timers.append(time.time())
			#print("sent : " + word[:word.find('~')] + " " + str(un_acks))
		lock.release()

		if(retrans > 8 or succ_send >= MAX_PACKETS):
			break

# packet reciever

def recv_acks():
	
	global un_acks
	global timers
	global succ_send
	global retrans
	global RTT_avg
	global tot_time
	global next_pack_id
	
	while (True):
		
		data, addr = sock_ack.recvfrom(1024)

		if(data != None):
			val = int(data.decode('utf-8'))
			if(val == -1):
				break
			if(val == next_pack_id):
				while(True):
					if(len(timers) > 0):
						break
				time_val = (time.time() - timers[0])
				tot_time += time_val
				del timers[0]
				#print("success : " + str(succ_send))
				succ_send += 1
				RTT_avg = tot_time/succ_send
				debug[val].append(time_val)
				debug[val].append(retrans)
				retrans = 0
				next_pack_id += 1
				lock.acquire()
				del buffer[0]
				un_acks -= 1
				lock.release()

		if(retrans > 8 or succ_send >= MAX_PACKETS):
			break

#data

sock = socket.socket(socket.AF_INET, # Internet
					 socket.SOCK_DGRAM) # UDP
sock_ack = socket.socket(socket.AF_INET, # Internet
					 socket.SOCK_DGRAM) # UDP
sock_ack.bind((R_ADDRESS, OTHER_PORT))

buffer = []
create_id = 0

un_acks = 0
next_pack_id = 0
timers = []
sent_count = 0

retrans = 0
succ_send = 0
tot_time = 0
RTT_avg = 0

debug = [[] for i in range(MAX_PACKETS)]


# process

t1 = threading.Thread(target = gen_packs,args = ())
t2 = threading.Thread(target = send_packs,args = ())
t3 = threading.Thread(target = recv_acks,args = ())

lock = threading.Lock()

t1.start()
t2.start()
t3.start()


while(True):

	lock.acquire()
	if(len(timers) > 0):
		if(succ_send > 10):
			if((time.time() - timers[0]) > 2*RTT_avg):
				timers.clear()
				un_acks = 0
				retrans += 1
		else:
			if((time.time() - timers[0]) > 0.1):
				timers.clear()
				un_acks = 0
				retrans += 1
	lock.release()
	
	if(retrans > 10 or succ_send >= MAX_PACKETS):
		break

t1.join()
t2.join()
t3.join()

if(DEBUG_MODE):
	j = 0
	for pac in debug:
		print(str(j) + " : ",end="")
		print(pac)
		j += 1

print("PACKET_GEN_RATE : " + str(PACKET_GEN_RATE))
print("PACKET_LENGTH : " + str(PACKET_LENGTH))
print("Retransmission Ratio : ",end="")
print(sent_count/succ_send)
print("AVG RTT : ",end="")
print(RTT_avg)

print("Sender Terminated")