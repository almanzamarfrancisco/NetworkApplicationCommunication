import socket
import json
import random

HOST = "192.168.0.13"
PORT = 8090 
bufferSize = 1024
message = ""

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
	s.bind((HOST, PORT))
	message = "*Not found*"
	while (True):
		data, address = s.recvfrom(bufferSize)
		dd = data.decode()
		dds = dd.split('.')
		print(f"Searching for: {dd}")
		print(f"Client IP: {address}")
		f = open("cctld.json")
		hosts = json.load(f)
		f.close()
		n = random.randint(0,len(hosts))
		for i, host in enumerate(hosts):
			print(f"Searching for .{dds[len(dds)-1]} ip address")
			if host['host_name'] == "i.mx-ns.mx":
				message = json.dumps(host)
				break
		bytesToSend = str.encode(message)
		s.sendto(bytesToSend, address)
