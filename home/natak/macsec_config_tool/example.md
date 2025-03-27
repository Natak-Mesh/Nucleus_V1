PEER #1
ip link add link end0 macsec0 type macsec encrypt on
My peer
ip macsec add macsec0 tx sa 0 pn 1 on key 01 3B11A9E2BB3C4A056D791372D8A0A770

Another peer #1
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f sa 0 pn 1 on key 00 E33750401518247FAC2D42110258CB4B

Another peer #2
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61 sa 0 pn 1 on key 00 65C130312D4D748B2A072D6EB260CBCF

ip link set macsec0 up
ip addr add 10.100.0.10/24 dev macsec0


#
PEER #2
ip link add link end0 macsec0 type macsec encrypt on
My peer
ip macsec add macsec0 tx sa 0 pn 1 on key 01 E33750401518247FAC2D42110258CB4B

Another peer #1
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f sa 0 pn 1 on key 00 3B11A9E2BB3C4A056D791372D8A0A770

Another peer #2
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61 sa 0 pn 1 on key 00 65C130312D4D748B2A072D6EB260CBCF

ip link set macsec0 up
ip addr add 10.100.0.11/24 dev macsec0


#
PEER #3
ip link add link end0 macsec0 type macsec encrypt on
My peer
ip macsec add macsec0 tx sa 0 pn 1 on key 01 65C130312D4D748B2A072D6EB260CBCF

Another peer #1
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f
ip macsec add macsec0 rx port 1 address f0:2f:74:d0:2c:1f sa 0 pn 1 on key 00 E33750401518247FAC2D42110258CB4B

Another peer #2
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61
ip macsec add macsec0 rx port 1 address 4c:36:4e:84:2c:61 sa 0 pn 1 on key 00 3B11A9E2BB3C4A056D791372D8A0A770

ip link set macsec0 up
ip addr add 10.100.0.12/24 dev macsec0