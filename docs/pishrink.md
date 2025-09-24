use lsblk to find what the pi disk is mounted as (sdX) set output file to whatever you want

sudo dd if=/dev/sdc of=~/node_1_unconfigured_takserver.img bs=4M status=progress conv=fsync

# install pishrink
sudo apt update
sudo apt install git p7zip-full
git clone https://github.com/Drewsif/PiShrink.git
cd PiShrink
sudo cp pishrink.sh /usr/local/bin/pishrink
sudo chmod +x /usr/local/bin/pishrink


sudo pishrink node_1_unconfigured_takserver.img
# make sure you're in the directory with the .img you're trying to shrink
