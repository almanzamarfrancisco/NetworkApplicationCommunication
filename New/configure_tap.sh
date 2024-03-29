#! /bin/bash
wlp4s0_ip=`ip addr show wlp4s0 | awk '$1 == "inet" {gsub(/\/.*$/, "", $2); print $2}'`
mask=`ip -o -f inet addr show wlp4s0 | awk '/scope global/ {print $4}' | grep -o '[^/]*$'`
read -p "Enter Gateway ip: " gateway_ip
# gateway_ip=$(/sbin/ip route | awk '/default/ { print $3 }')
network_id=$(/sbin/ip route | awk '/scope/ { print $1 }')
echo "[I] Configuring tap0 with tunctl"
sudo tunctl -d tap0
sudo tunctl -t tap0
echo "[I] Done! :)"
echo "[I] wlps4s0 ip: $wlp4s0_ip"
readarray -d . -t ipstr <<<"$wlp4s0_ip"
node_str="${ipstr[3]}"
node=$((node_str))
if [[ node < 254 ]]
then
	node=$((node-1))
else
	node=$((node+1))
fi
ipstr="${ipstr[0]}.${ipstr[1]}.${ipstr[2]}.$node"
echo "[I] Configuring ip in tap0: $ipstr/$mask"
sudo ip address add $ipstr/$mask dev tap0
echo "[I] Setting up tap0..."
sudo ip link set dev tap0 up
# ip route add <network_ip_id>/<cidr> via <gateway_ip> dev <network_card_name>
# sudo ip route del 192.168.100.10/32 via 192.168.100.1 dev wlp4s0
# sudo ip addr del <network_ip>/<cidr> dev tap0
echo "[I] Adding $network_id to ip route table with gateway ip: $gateway_ip on dev tap0 *onlink*"
sudo ip route add $network_id via $gateway_ip dev tap0 onlink
sudo ip route add 192.168.1.0/24 via $gateway_ip dev tap0 onlink
sudo ip route add 192.168.2.0/24 via $gateway_ip dev tap0 onlink
sudo ip route add 192.168.3.0/24 via $gateway_ip dev tap0 onlink
sudo ip route add 192.168.8.0/30 via $gateway_ip dev tap0 onlink
sudo ip route add 192.168.9.0/30 via $gateway_ip dev tap0 onlink
# sudo route add default gw $gateway_ip tap0

echo "[I] Done!"
# ping -I tap0 192.168.1.5 # IMPORTANT Select interface for pingging