#!/bin/bash

# Setup Script for Announcer
#
# This script is intended to be distributed alongside a pre-built binary.

set -e

chmod +x ./announcer
cp ./announcer /usr/local/bin
if [ $? != 0 ]; then
    echo "Failed to copy to /usr/local/bin!"
    exit 1
fi;

VERSION="2.0.11"
if [ $? != 0 ]; then
    echo "Failed to test billboard_announcer!"
    exit 1
fi;

echo "Setup complete!  Version installed:  ${VERSION}"

