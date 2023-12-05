#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEMD_PATH="/home/dev/.config/systemd/user"
JACK_NAME="jackd.service"
JACK_PATH="$DIR/$JACK_NAME"
JACK_DEST="$SYSTEMD_PATH/$JACK_NAME"

cp $JACK_PATH $JACK_DEST

systemctl --user daemon-reload
systemctl  --user enable $JACK_NAME

# Start the service
systemctl --user start $JACK_NAME

echo "Service $JACK_NAME installed and started successfully."