Some notes for cert creation from the docker version of the install. not valid on Pi, but could be useful


for metadata script
note no space after =
 country =US
 state =FL
 city ="Tampa" note the quotation marks
 organization =NatakMesh
 unit =TAK
sudo nano tak/certs/cert-metadata.sh

-create root cert
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeRootCa.sh --ca-name NATAK-ROOT-CA-01"

-create intermediate cert
docker exec -it takserver bash -c "cd /opt/tak/certs && echo y |./makeCert.sh ca NATAK-ID-CA-01"

-create server cert
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh server takserver"

sed -i "s/truststore-root/truststore-NATAK-ID-CA-01/g" tak/CoreConfig.xml

docker restart takserver && tail -f tak/logs/takserver-messaging.log

-create web admin cert
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh client1 webadmin"

-modify webadmin to be an admin
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar certmod -A /opt/tak/certs/files/webadmin.pem"

-password must be 15 characters, include capital and special character. had an issue with ! but it accepted
-password with _
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar usermod -A -p '{PASSWORD}' webadmin"

-create a client cert, for something like wintak or (i think) an EUD this example will name the cert wintak01
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh client wintak01

-assign client to usergroup
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar certmod /opt/tak/certs/files/wintak01.pem"

-to copy intermediate cert, this renames the int cert to caCert
cp takserver-docker-5.3-RELEASE-30/tak/certs/files/truststore-NATAK-ID-CA-01.p12 caCert.p12

-to copy webadmin cert dont forget the trailing "."
cp takserver-docker-5.3-RELEASE-30/tak/certs/files/webadmin.p12 .

- to copy client cert
sudo cp takserver-docker-5.3-RELEASE-30/tak/certs/files/wintak01.p12 .

-need to change ownership of certs so you can move this to EUD/browser
-get into same directory, in this example user is nate
sudo chown nate:nate {name/path of cert}

- move intermediate (caCert.p12 in this case) and clientx.p12 cert to client then set up in atak
- use takserver host machine IP, not docker container IP during setup
- remember password is atakatak  use ssl


-webadmin cert is uploaded to web brower. Web interface @port 8443, remember must use https://
-to find IP of takeserver docker container use below, this assumes container is actually named takserver
- docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' takserver
