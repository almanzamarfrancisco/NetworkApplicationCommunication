#! /bin/bash
read -p "Enter R1 ip: " r1_ip
echo "[I] Getting $r1_ip"
tftp -4 -m binary $r1_ip -c get r1-config
echo "    [I] Done!"
echo "[I] Getting 192.168.8.2..."
tftp -4 -m binary 192.168.8.2 69 -c get r2-config
echo "    [I] Done!"
echo "[I] Getting 192.168.9.2..."
tftp -4 -m binary 192.168.9.2 69 -c get r3-config
echo "    [I] Done!"