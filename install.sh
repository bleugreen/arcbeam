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
    libjack-dev python3 python3-pip python3-gpiozero python3-setuptools cmake libglib2.0-dev libcairo2-dev libgirepository1.0-dev redis \
    gpiod libgpiod-dev jackd i2c-tools python3-libgpiod yq alsa-tools
}

setup_audio(){
    sudo usermod -a -G audio $USER
    echo '@audio - rtprio 95' | sudo tee -a /etc/security/limits.conf
    echo '@audio - memlock unlimited' | sudo tee -a /etc/security/limits.conf
}

install_nqptp(){
    cd ~
    git clone https://github.com/mikebrady/nqptp.git
    cd nqptp
    autoreconf -fi
    ./configure --with-systemd-startup
    make
    sudo make install
    sudo systemctl enable nqptp
    sudo systemctl start nqptp
}

install_alac() {
    cd ~
    git clone https://github.com/mikebrady/alac.git
    cd alac
    autoreconf -fi && ./configure && sudo make && sudo make install && sudo ldconfig
}

install_shairport() {
    cd ~
    git clone https://github.com/mikebrady/shairport-sync.git
    cd shairport-sync
    autoreconf -fi
    ./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2 \
    --with-apple-alac --with-metadata --with-jack
    make
    sudo make install
}

install_python() {
    cd ~
    python -m venv env --system-site-packages
    source env/bin/activate
    pip install numpy Cython pycairo RPi.GPIO adafruit-blinka
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_serial_hw 0
    sudo raspi-config nonint do_ssh 0
    sudo raspi-config nonint disable_raspi_config_at_boot 0
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
    sudo cp services/shairport-sync.conf /etc/shairport-sync.conf
    sudo cp services/asound.conf /etc/asound.conf
    echo "sudo systemctl start arcbeam.service" >> ~/.bash_profile
    pip install -r requirements.txt
}

main() {
    update_system
    install_deps
    install_nqptp
    max_attempts=3
    attempt=0

    # Retry loop
    while [ $attempt -lt $max_attempts ]; do
        install_alac
        exit_status=$?

        if [ $exit_status -eq 0 ]; then
            echo "Function succeeded."
            break
        else
            echo "Function failed. Attempt $((attempt+1))/$max_attempts."
            attempt=$((attempt+1))
            sleep 1 # Delay for 1 second before retrying
        fi
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "Function failed after $max_attempts attempts."
    fi

    install_shairport
    install_python
    install_eink_libs
    setup_arcbeam
    setup_audio
}

main
sudo reboot