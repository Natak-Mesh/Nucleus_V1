wpa_3 establishment is very inconcistent.
looked at timesyncd as a potential issue, tried to fix by disabling it in batmesh and setting a default date/time. But it may be that
wpa_supplicant needs the date/times to be very close for it to work. Seems like this may not be the case
as I can still get ESTAB for wpa_3 occasionally, but something is definitely gotten bad.
next 2 steps
1. move the mesh establishment back to script, use wpa_supplicant only to handle encryption
2. setup chrony to run after mesh establishment and before wpa_supplicant, try to get clocks synced ahead of time
