import socket
import json

HOST = "192.168.0.13"
PORT = 9010 
bufferSize = 1024
message = ""

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
	s.bind((HOST, PORT))
	message = "*Not found*"
	while (True):
		data, address = s.recvfrom(bufferSize)
		dd = data.decode()
		print(f"Searching for: {dd}")
		print(f"Client IP: {address}")
		f = open('domain_name_space.json')
		hosts = json.load(f)
		f.close()
		for host in hosts:
			print(f"Searching for .{dd} ip address")
			if host['host_name'] == dd:
				message = json.dumps(host)
				break
		bytesToSend = str.encode(message)
		s.sendto(bytesToSend, address)
