Some notes for cert creation from the docker version of the install. not valid on Pi, but could be useful


for metadata script
note no space after =<br>
 country =US<br>
 state =FL<br>
 city ="Tampa" note the quotation marks<br>
 organization =NatakMesh<br>
 unit =TAK<br>
sudo nano tak/certs/cert-metadata.sh<br>

-create root cert<br>
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeRootCa.sh --ca-name NATAK-ROOT-CA-01"<br>

-create intermediate cert<br>
docker exec -it takserver bash -c "cd /opt/tak/certs && echo y |./makeCert.sh ca NATAK-ID-CA-01"<br>

-create server cert<br>
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh server takserver"<br>

sed -i "s/truststore-root/truststore-NATAK-ID-CA-01/g" tak/CoreConfig.xml<br>

docker restart takserver && tail -f tak/logs/takserver-messaging.log<br>

-create web admin cert<br>
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh client1 webadmin"<br>

-modify webadmin to be an admin<br>
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar certmod -A /opt/tak/certs/files/webadmin.pem"<br>

-password must be 15 characters, include capital and special character. had an issue with ! but it accepted<br>
-password with _<br>
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar usermod -A -p '{PASSWORD}' webadmin"<br>

-create a client cert, for something like wintak or (i think) an EUD this example will name the cert wintak01<br>
docker exec -it takserver bash -c "cd /opt/tak/certs && ./makeCert.sh client wintak01<br>

-assign client to usergroup<br>
docker exec -it takserver bash -c "java -jar /opt/tak/utils/UserManager.jar certmod /opt/tak/certs/files/wintak01.pem"<br>

-to copy intermediate cert, this renames the int cert to caCert<br>
cp takserver-docker-5.3-RELEASE-30/tak/certs/files/truststore-NATAK-ID-CA-01.p12 caCert.p12<br>

-to copy webadmin cert dont forget the trailing "."<br>
cp takserver-docker-5.3-RELEASE-30/tak/certs/files/webadmin.p12 .<br>

- to copy client cert<br>
sudo cp takserver-docker-5.3-RELEASE-30/tak/certs/files/wintak01.p12 .<br>

-need to change ownership of certs so you can move this to EUD/browser<br>
-get into same directory, in this example user is nate<br>
sudo chown nate:nate {name/path of cert}<br>

- move intermediate (caCert.p12 in this case) and clientx.p12 cert to client then set up in atak<br>
- use takserver host machine IP, not docker container IP during setup<br>
- remember password is atakatak  use ssl<br>


-webadmin cert is uploaded to web brower. Web interface @port 8443, remember must use https://<br>
-to find IP of takeserver docker container use below, this assumes container is actually named takserver<br>
- docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' takserver<br>
