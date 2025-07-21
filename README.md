wpa3 establishment great with the new script. now we're dealing with mt76 overcurrent bug issues.

I'm seeing "overcurrent failures in the 400-600 second mark. no idea why this is coming up now 
I thought maybe it was the 6.12 kernel, but rolling back to 6.6 didnt help
then i looked at my Pi->card cabling thinking maybe that was the issue
tried multiple versions, even tried the one that came with the card. No good. <br>

Error message:<br> 
`vendor request req:07 off:XXXX failed:-71
tx urb failed: -71`<br>
along with overcurrent warnings on all USB ports. <br>
`usb usb2-portX: over-current change #X`<br>

 
### Other Reports<br>
- Raspberry Pi Forum: “MT76 USB dongle fails with -71 after idle, only fix is replug.”  <br>
[forums.raspberrypi.com](https://forums.raspberrypi.com/viewtopic.php?t=385383)<br>
- GitHub Discussions: “Flood of vendor request failures after kernel 5.x.” <br> 
[github.com/morrownr/USB-WiFi/issues/213](https://github.com/morrownr/USB-WiFi/issues/213)<br>
- OpenWRT Patch Notes: “Fix regression with resume on mt76x0u USB devices.”<br>


### Possible Fix <br>
Disable aggressive USB control retry flood in mt76 driver.

`echo 'options mt76 usb_rr_retry=0' | sudo tee /etc/modprobe.d/mt76.conf`<br>

`sudo update-initramfs -u`<br>
`sudo reboot`<br>


the mt76 driver usb retry fix seems to have worked 7/19/25
ran testing all day for stability 7/20, no issues
