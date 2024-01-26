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

install_deps () {
    apt install -y build-essential git autoconf automake libtool lsb-release curl gpg \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev \
    libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev libgcrypt-dev xxd \
    libjack-dev python3-pip python3-gpiozero cmake libglib2.0-dev libcairo2-dev libgirepository1.0-dev redis \

    curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
    sudo apt-get update
    sudo apt-get install redis
    systemctl enable redis-server.service
    systemctl enable redis.service
}

install_nqptp(){
    cd ~
    git clone https://github.com/mikebrady/nqptp.git
    cd nqptp
    autoreconf -fi
    ./configure --with-systemd-startup
    make
    make install
    systemctl enable nqptp
    systemctl start nqptp
}

install_alac() {
    cd ~
    git clone https://github.com/mikebrady/alac.git
    cd alac
    autoreconf -fi
    ./configure
    make
    make install
    ldconfig
}

install_shairport() {
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
    cd ~/arcbeam
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
    systemctl restart getty@tty1.service
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
    install_deps
    install_nqptp
    install_alac
    install_shairport
    install_python
    setup_arcbeam
}

main