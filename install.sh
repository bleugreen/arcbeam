#!/bin/bash

# Function to update and upgrade the system
update_system() {
    sudo apt-get update
    sudo apt-get upgrade -y
}

install_deps () {
    sudo apt install -y build-essential git autoconf automake libtool lsb-release curl gpg \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev \
    libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev libgcrypt-dev xxd \
    libjack-dev python3-pip python3-gpiozero cmake libglib2.0-dev libcairo2-dev libgirepository1.0-dev redis \
    gpiod libgpiod-dev jackd
}

install_nqptp(){
    cd ~
    git clone https://github.com/mikebrady/nqptp.git
    cd nqptp
    autoreconf -fi
    ./configure --with-systemd-startup
    sudo make
    sudo make install
    sudo systemctl enable nqptp
    sudo systemctl start nqptp
}

install_alac() {
    cd ~
    git clone https://github.com/mikebrady/alac.git
    cd alac
    autoreconf -fi
    ./configure
    sudo make
    sudo make install
    sudo ldconfig
}

install_shairport() {
    cd ~
    git clone https://github.com/mikebrady/shairport-sync.git
    cd shairport-sync
    autoreconf -fi
    ./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2 \
    --with-apple-alac --with-metadata --with-jack
    sudo make
    sudo make install
}

install_python() {
    sudo apt install -y  --upgrade python3-setuptools
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
        sudo cp "$service_file" /etc/systemd/system/
        local service_name=$(basename "$service_file")
        if [ "$service_name" != "$exclude_service" ]; then
            sudo systemctl daemon-reload
            sudo systemctl enable "$service_name"
        fi
    done
    sudo cp "$source_dir"/autologin.conf /etc/systemd/system/getty@tty1.service.d/
    sudo systemctl daemon-reload
    sudo systemctl restart getty@tty1.service
}

install_eink_libs() {
    cd ~
    wget https://github.com/joan2937/lg/archive/master.zip
    unzip master.zip
    cd lg-master
    sudo make
    sudo make install

    cd ~
    wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz
    tar zxvf bcm2835-1.71.tar.gz
    cd bcm2835-1.71/
    sudo ./configure && sudo make && sudo make check && sudo make install
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
    install_eink_libs
    setup_arcbeam
}

main