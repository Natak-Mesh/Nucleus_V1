# TAK Server Federation Guide

This guide provides step-by-step instructions for federating two TAK servers running on Raspberry Pi 4 devices, using certificates from the same certificate authority.

## Prerequisites

- Two Raspberry Pi 4 devices running TAK server
- Desktop PC with root certificate
- Intermediate certificates already installed on both Pi devices
- All devices connected via WiFi mesh network


## Certificate Creation and Federation Process


### Step 0: Create Root and Intermediate Certificates (ON DESKTOP PC)

1. **ON DESKTOP PC: Generate a root private key:**
   openssl genrsa -out root_key.pem 4096

2. **ON DESKTOP PC: Create a self-signed root certificate:**
   openssl req -x509 -new -nodes -key root_key.pem -sha256 -days 3650 -out root_cert.pem
   (When prompted, enter details for your Certificate Authority. The Common Name should be something like "My TAK Root CA")

3. **ON DESKTOP PC: Create an intermediate private key:**
   openssl genrsa -out intermediate_key.pem 4096

4. **ON DESKTOP PC: Create an intermediate certificate request:**
   openssl req -new -key intermediate_key.pem -out intermediate_request.csr
   (When prompted, enter details for your intermediate CA. The Common Name should be different from the root CA, like "My TAK Intermediate CA")

5. **ON DESKTOP PC: Sign the intermediate certificate with the root certificate:**
   openssl x509 -req -in intermediate_request.csr -CA root_cert.pem -CAkey root_key.pem -CAcreateserial -out intermediate_cert.pem -days 1825

6. **ON DESKTOP PC: Copy the intermediate certificate to both Pi devices:**
   scp intermediate_cert.pem pi@SERVER_A_IP:/tmp/
   scp intermediate_cert.pem pi@SERVER_B_IP:/tmp/

7. **ON EACH PI: Move the intermediate certificate to the TAK directory:**
   sudo mv /tmp/intermediate_cert.pem /opt/tak/certs/files/
   sudo chown tak:tak /opt/tak/certs/files/intermediate_cert.pem
   sudo chmod 640 /opt/tak/certs/files/intermediate_cert.pem


### Step 1: Create Server Certificates (ALL ON DESKTOP PC)

1. **ON DESKTOP PC: Generate a private key for Server A:**
   ```bash
   openssl genrsa -out serverA_key.pem 2048
   ```

2. **ON DESKTOP PC: Create a certificate request for Server A:**
   ```bash
   openssl req -new -key serverA_key.pem -out serverA_request.csr
   ```
   (When prompted, enter details like Common Name = "Server A" or its IP address)

3. **ON DESKTOP PC: Sign the request with your intermediate cert:**
   ```bash
   openssl x509 -req -in serverA_request.csr -CA intermediate_cert.pem -CAkey intermediate_key.pem -CAcreateserial -out serverA_cert.pem -days 365
   ```

4. **ON DESKTOP PC: Repeat steps 1-3 for Server B**
   ```bash
   openssl genrsa -out serverB_key.pem 2048
   openssl req -new -key serverB_key.pem -out serverB_request.csr
   openssl x509 -req -in serverB_request.csr -CA intermediate_cert.pem -CAkey intermediate_key.pem -CAcreateserial -out serverB_cert.pem -days 365
   ```

### Step 2: Copy Files (FROM DESKTOP PC TO EACH PI)

1. **ON DESKTOP PC: Copy files to Pi Server A:**
   ```bash
   scp serverA_cert.pem serverA_key.pem pi@SERVER_A_IP:/tmp/
   ```

2. **ON DESKTOP PC: Copy files to Pi Server B:**
   ```bash
   scp serverB_cert.pem serverB_key.pem pi@SERVER_B_IP:/tmp/
   ```

### Step 3: Move Files on Each Pi

1. **ON PI SERVER A: Move files to TAK directory:**
   ```bash
   sudo mv /tmp/serverA_cert.pem /tmp/serverA_key.pem /opt/tak/certs/files/
   sudo chown tak:tak /opt/tak/certs/files/serverA_*.pem
   sudo chmod 640 /opt/tak/certs/files/serverA_*.pem
   ```

2. **ON PI SERVER B: Move files to TAK directory:**
   ```bash
   sudo mv /tmp/serverB_cert.pem /tmp/serverB_key.pem /opt/tak/certs/files/
   sudo chown tak:tak /opt/tak/certs/files/serverB_*.pem
   sudo chmod 640 /opt/tak/certs/files/serverB_*.pem
   ```

### Step 4: Configure Each Server

1. **ON PI SERVER A: Edit the CoreConfig.xml file:**
   ```bash
   sudo nano /opt/tak/CoreConfig.xml
   ```
   
   Add this inside the `<federation>` section (create it if it doesn't exist):
   ```xml
   <federateWith>
     <connection>
       <address>IP_OF_SERVER_B</address>
       <port>8443</port>
       <clientCertificate>/opt/tak/certs/files/serverA_cert.pem</clientCertificate>
       <clientKey>/opt/tak/certs/files/serverA_key.pem</clientKey>
       <caCertificate>/opt/tak/certs/files/intermediate_cert.pem</caCertificate>
     </connection>
   </federateWith>
   ```

2. **ON PI SERVER B: Edit the CoreConfig.xml file:**
   ```bash
   sudo nano /opt/tak/CoreConfig.xml
   ```
   
   Add this inside the `<federation>` section (create it if it doesn't exist):
   ```xml
   <federateWith>
     <connection>
       <address>IP_OF_SERVER_A</address>
       <port>8443</port>
       <clientCertificate>/opt/tak/certs/files/serverB_cert.pem</clientCertificate>
       <clientKey>/opt/tak/certs/files/serverB_key.pem</clientKey>
       <caCertificate>/opt/tak/certs/files/intermediate_cert.pem</caCertificate>
     </connection>
   </federateWith>
   ```

### Step 5: Restart Both Servers

1. **ON PI SERVER A: Restart TAK server:**
   ```bash
   sudo systemctl restart takserver
   ```

2. **ON PI SERVER B: Restart TAK server:**
   ```bash
   sudo systemctl restart takserver
   ```

## Federation with More Than 2 Servers

For a flat federation topology with multiple servers on the same layer 2 mesh network:

1. **Create certificates for each server** following Step 1 above
2. **Copy the appropriate certificates to each server** following Steps 2-3 above
3. **On each server, configure connections to ALL other servers** in the federation

For example, if you have 3 servers (A, B, and C), Server A's CoreConfig.xml would include:

```xml
<federateWith>
  <connection>
    <!-- Connection to Server B -->
    <address>IP_OF_SERVER_B</address>
    <port>8443</port>
    <clientCertificate>/opt/tak/certs/files/serverA_cert.pem</clientCertificate>
    <clientKey>/opt/tak/certs/files/serverA_key.pem</clientKey>
    <caCertificate>/opt/tak/certs/files/intermediate_cert.pem</caCertificate>
  </connection>
  <connection>
    <!-- Connection to Server C -->
    <address>IP_OF_SERVER_C</address>
    <port>8443</port>
    <clientCertificate>/opt/tak/certs/files/serverA_cert.pem</clientCertificate>
    <clientKey>/opt/tak/certs/files/serverA_key.pem</clientKey>
    <caCertificate>/opt/tak/certs/files/intermediate_cert.pem</caCertificate>
  </connection>
</federateWith>
```

## Troubleshooting

If federation fails, check:

1. **Network connectivity:**
   ```bash
   ping IP_OF_OTHER_SERVER
   ```

2. **Certificate permissions:**
   ```bash
   ls -la /opt/tak/certs/files/
   ```
   Ensure certificates are owned by the tak user and have appropriate permissions

3. **TAK server logs:**
   ```bash
   sudo journalctl -u takserver -f
   ```
   Look for federation-related errors or connection issues

4. **Firewall settings:**
   ```bash
   sudo iptables -L
   ```
   Ensure port 8443 is open for federation traffic
