#since the pi's 200 subnet wont let you directly connect to the internet , these are some commands to get the pi online if needed.
                                                                                                   
                                                                                                     
#this is all pretty ugly, but seems to work. this assumes your PC
#is connected to the Pi via an ethernet (eth0) connection
# and that you are connected to your internet capable network
# via your wifi (wlan0)
# you need your eth0 IP address (use command "ip a" from terminal) for the command to run on the pi

#run this on your PC, adjust interface names as needed
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -p
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

#then run this on pi. make sure nameserver is set in resolve.conf then run the route add command in terminal , use   address from PC
#sudo nano /etc/resolv.conf
#nameserver 8.8.8.8
#
# sudo ip route add default via <PC_Ethernet_IP>
# example: sudo ip route add default via 192.168.200.20


# I was having trouble at one point, ended up adding this to the PC script. probably not necessary, just mostly a duplicate of above commands
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -j ACCEPT

#the above worked ..maybe try that if original scrip fails


