# PiShrink fstab Issue Fix

## Problem
PiShrink'd image causes reboot loop and read-only filesystem on new hardware.

## Error Messages
Check with journalctl:
```bash
sudo journalctl -f
# Shows:
startup_sequence.sh: /var/log/rnsd.log: Read-only file system
systemd-hostnamed.service: Failed to set up mount namespacing: Read-only file system
Broadcast message from root: The system will reboot now!
```

## Root Cause
PiShrink expansion script in `/etc/rc.local` gets stuck in loop, wipes `/etc/fstab`.

## Fix

### During reboot loop:
```bash
sudo mount -o remount,rw /
echo '#!/bin/bash' | sudo tee /etc/rc.local
sudo resize2fs /dev/mmcblk0p2
```

### Create proper fstab:
```bash
sudo tee /etc/fstab << 'EOF'
proc            /proc           proc    defaults          0       0
/dev/mmcblk0p1  /boot/firmware  vfat    defaults          0       2
/dev/mmcblk0p2  /               ext4    defaults,noatime  0       1
EOF
```

### Prevention (before running PiShrink):
```bash
# Verify fstab exists
cat /etc/fstab

# If empty, create it with the above content
# Ensure rc.local.bak exists for clean restore
