#! /bin/bash
wslp4s0_ip=`ip addr show wlp4s0 | awk '$1 == "inet" {gsub(/\/.*$/, "", $2); print $2}'`
mask=`ip -o -f inet addr show wlp4s0 | awk '/scope global/ {print $4}' | grep -o '[^/]*$'`
echo "[I] wlps4s0 ip: $wslp4s0_ip"
readarray -d . -t ipstr <<<"$wslp4s0_ip"
node_str="${ipstr[3]}"
node=$((node_str))
if [[ node < 254 ]]
then
	node=$((node-1))
else
	node=$((node+1))
fi
ipstr="${ipstr[0]}.${ipstr[1]}.${ipstr[2]}.$node"
echo "[I] Configuring ip: $ipstr/$mask"
# ip route add <network_ip>/<cidr> via <gateway_ip> dev <network_card_name>
sudo ip address add $ipstr/$mask dev tap0
echo "[I] Done!"