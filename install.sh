#!/bin/bash

# Ensuring the script is run as root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Function to update and upgrade the system
update_system() {
    apt-get update
    apt-get upgrade -y
}

install_shairport() {
    apt install --no-install-recommends -y build-essential git autoconf automake libtool \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev \
    libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev libgcrypt-dev xxd libjack-dev

    git clone https://github.com/mikebrady/nqptp.git
    cd nqptp
    autoreconf -fi
    ./configure --with-systemd-startup
    make
    make install
    cd ~

    git clone https://github.com/mikebrady/alac.git
    cd alac
    autoreconf -fi
    ./configure --with-systemd-startup
    make
    make install
    cd ~

    git clone https://github.com/mikebrady/shairport-sync.git
    cd shairport-sync
    autoreconf -fi
    ./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2 \
    --with-apple-alac --with-metadata --with-jack
    make
    make install
}

install_python() {
    apt-get install -y python3-pip python3-gpiozero cmake libglib2.0-dev libcairo2-dev libgirepository1.0-dev redis
    apt install -y  --upgrade python3-setuptools
    cd ~
    python -m venv env --system-site-packages
    source env/bin/activate
    pip install numpy Cython pycairo
    pip install --upgrade adafruit-python-shell
    wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
    sudo -E env PATH=$PATH python3 raspi-blinka.py
}

deploy_systemd_services() {
    local source_dir="services/systemctl"  # Update this path if necessary
    local exclude_service="arcbeam.service"
    # Copy each .service file and enable it
    for service_file in "$source_dir"/*.service; do
        cp "$service_file" /etc/systemd/system/
        local service_name=$(basename "$service_file")
        if [ "$service_name" != "$exclude_service" ]; then
            systemctl daemon-reload
            systemctl enable "$service_name"
        fi
    done
    cp "$source_dir"/autologin.conf /etc/systemd/system/getty@tty1.service.d/
    systemctl daemon-reload
}

setup_arcbeam() {
    cd ~
    git clone https://github.com/Mitchell57/arcbeam.git
    cd arcbeam
    deploy_systemd_services
    cp services/shairport-sync.conf /etc/shairport-sync.conf
    echo "sudo systemctl start arcbeam.service" >> ~/.bash_profile
    pip install -r requirements.txt
}

main() {
    update_system
    install_dependencies
    install_shairport
    install_python
    setup_arcbeam
}

main