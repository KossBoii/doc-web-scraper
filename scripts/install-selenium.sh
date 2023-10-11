#!/usr/bin/bash

echo "Update the repository and any packages..."
sudo apt update && sudo apt upgrade -y

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

chrome_version=($(google-chrome --version))
echo "Chrome version: ${chrome_version[2]}"

wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/117.0.5938.149/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/bin/
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver

chromedriver --version
which chromedriver # should be /usr/bin/chromedriver
rm chromedriver-linux64.zip
rm -rf chromedriver-linux64
