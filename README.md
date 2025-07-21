wpa3 establishment great with the new script. now we're dealing with mt76 overcurrent bug issues.

it seems there is an issue post kernel 5.15 with these mt76 cards and extended use.
I'm seeing "overcurrent failures in the 400-600 second mark. no idea why this is coming up now 
I thought maybe it was the 6.12 kernel, but rolling back to 6.6 didnt help
then i looked at my Pi->card cabling thinking maybe that was the issue
tried multiple versions, even tried the one that came with the card. No good.

Error message: 
`vendor request req:07 off:XXXX failed:-71
tx urb failed: -71`
along with overcurrent warnings on all USB ports. 
`usb usb2-portX: over-current change #X`

 

See below for notes
# 📝 Summary: mt76x0u USB -71 Errors on Pi OS

##  Issue
- MediaTek MT76x0U adapters (`mt76x0u` driver) failing with:
vendor request req:07 off:XXXX failed:-71
tx urb failed: -71

- Pi4 logs also show `usb usb2-portX: over-current change #X`.
- Started recently after years of stable use.

##  Other Reports
- Raspberry Pi Forum: “MT76 USB dongle fails with -71 after idle, only fix is replug.”  
[forums.raspberrypi.com](https://forums.raspberrypi.com/viewtopic.php?t=385383)
- GitHub Discussions: “Flood of vendor request failures after kernel 5.x.”  
[github.com/morrownr/USB-WiFi/issues/213](https://github.com/morrownr/USB-WiFi/issues/213)
- OpenWRT Patch Notes: “Fix regression with resume on mt76x0u USB devices.”


## Possible Fix
Disable aggressive USB control retry flood in mt76 driver.

echo 'options mt76 usb_rr_retry=0' | sudo tee /etc/modprobe.d/mt76.conf

sudo update-initramfs -u
sudo reboot

## If this doesnt work rollback to kernel 5.15
## shouldnt affect anything we're doing

# the mt76 driver usb retry fix seems to have worked 7/19/25
