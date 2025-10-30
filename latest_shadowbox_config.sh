#!/bin/bash

# This script copies the latest shadowbox_config.json from the server to the
# current path so that in case the server goes down, the user keys can be
# copied to another server, and users will not lose access.
# In case your server goes down or becomes inaccessible, copy the
# shadowbox_config.json file to the path /opt/outline/persisted-state/ on your
# new server and install Outline there. Then change your domain's IP to
# point to the new server.
# In order to always have the latest shadowbox_config.json in the current path,
# add the following line to `crontab -e` so that this script is called every day
# at 10 AM.
# `0 10 * * * /home/user/OutlineKeyGenerator/latest_shadowbox_config.sh root@domain_name /home/user/ | logger -t latest_shadowbox_config.sh`
# Your public key needs to be added to the remote server so that SCP will not
# ask for your credentials.

useratIP=$1
destination_path=$2
sudo scp $useratIP:/opt/outline/persisted-state/shadowbox_config.json $destination_path
