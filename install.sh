#!/bin/sh

# script for installing justinbot onto a ubuntu machine
#    sets up config
#    installs requirements 
#    installs files (sounds and videos for gags)
#    sets up systemd to run justinbot on startup

# check for root (user id of 0)
 [ `id -u` -eq 0 ] && echo "this script should not be run as root" && exit 1

### make and set up config file
# get discord token from user
echo "get the bot's token from the discord dev portal and enter it here:"
read TOKEN 
# make a config file for inportant variables
echo "creating config file 'justinConfig.py'"
    cat > justinConfig.py <<CONFIGFILE
PREFIX = "!"
DISCORD_TOKEN = "$TOKEN"
BOT_DIR = "$PWD/"
CONFIGFILE

### install requirements
echo "installing pip with apt. . ."
sudo apt update && sudo apt install python3-pip -y || { echo "failed to install python3-pip, aborting. . ."; exit 1; }

# install python packages
echo "installing requirements with pip3. . ."
pip3 install -r requirements.txt || { echo "failed to install pip packages, aborting. . ."; exit 1; }


### instal files
# get files from release page of github when i put them there in the future LOLOLOLOLOL

### use systemd to run justinbot on system startup
echo "Setting up justin.py to run on system startup"
# make a unit file for this systemd service
echo "creating unit file 'justinbot.service'"
    cat > justinbot.service <<UNITFILE
[Unit]
Description=Runs justin bot on startup
Wants=network-online.target
After=network-online.target
[Service]
User=$(whoami)
Group=$(id -gn)
ExecStart=/usr/bin/python3 "$PWD/justin.py"
[Install]
WantedBy=multi-user.target
UNITFILE
# put the unitfile in its place w/ systemd
sudo mv justinbot.service /etc/systemd/system/justinbot.service
# reload systemd so it can find this newly created service
echo "reloding systemctl daemon"
sudo systemctl daemon-reload
# enable this service in systemd
echo "enabling justinbot.service"
sudo systemctl enable justinbot.service

echo "justin bot service has been added and enabled"
echo "justin.py will be automatically run on startup from now on"
echo ""
echo "to dissable running on startup type 'sudo systemctl disable justinbot.service'"
echo ""

exit 0