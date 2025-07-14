

DOCKER VERSION DOES NOT WORK ON PI, THIS DOES WORK ON PC THOUGH. IN PLACE OF DOCKER USE BARE METAL INSTALL FOR PI https://mytecknet.com/lets-build-a-tak-server/


Use takserver 5.3 docker from tak.gov

Looking at bringing Takserver onto each node. Set up to federate with other nodes. Cut down on multicast traffic and get us set up for video streaming etc

Install docker with<br>
curl -fsSL https://get.docker.com | sudo sh<br>

then <br>
sudo usermod -aG docker $USER
