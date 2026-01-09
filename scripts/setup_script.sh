#!/bin/bash
set -e

### System Update & Prerequisites
echo "[1/12] Updating system"
apt update
apt upgrade -y
apt full-upgrade -y

echo "[2/12] Installing development tools"
apt install -y python3-pip ffmpeg git curl cmake build-essential code # code to be removed in the final version of the script (used for debugging/development on the raspberry pi)

echo "[3/12] Installing libraries"
apt install -y libx264-dev libjpeg-dev

echo "[4/12] Installing GStreamer stack"
apt install -y \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    gstreamer1.0-qt5 \
    gstreamer1.0-pulseaudio


### Bootloader / EEPROM Update
echo "[5/12] Updating Raspberry Pi EEPROM"
rpi-eeprom-update -a || true


### Enable PCIe Gen 3.0 
echo "[6/12] Enabling PCIe Gen 3.0"

CONFIG_FILE="/boot/firmware/config.txt"
if ! grep -q "^dtparam=pciex1_gen=3" "$CONFIG_FILE"; then
    echo "dtparam=pciex1_gen=3" >> "$CONFIG_FILE"
fi


### Enable Latest Bootloader
echo "[7/12] Setting bootloader to latest stable"
BOOTCONF="/etc/default/rpi-eeprom-update"

if ! grep -q "FIRMWARE_RELEASE_STATUS=stable" "$BOOTCONF"; then
    sed -i 's/^FIRMWARE_RELEASE_STATUS=.*/FIRMWARE_RELEASE_STATUS=stable/' "$BOOTCONF"
fi


### Hailo Detection Function
detect_hailo_hat() {
    echo "Checking for Hailo HAT on PCIe"

    if command -v lspci >/dev/null 2>&1; then
        if lspci -nn | grep -qi "1e60"; then
            echo "Hailo device detected on PCIe bus."
            return 0
        else
            echo "No Hailo device detected."
            return 1
        fi
    else
        echo "lspci not installed. Installing pciutils"
        apt install -y pciutils
        if lspci -nn | grep -qi "1e60"; then
            echo "Hailo device detected on PCIe bus."
            return 0
        else
            echo "No Hailo device detected."
            return 1
        fi
    fi
}


### Conditional Hailo Installation
echo "[8/12] Checking for Hailo HAT"

if detect_hailo_hat; then
    echo "Installing Hailo packages"
    apt install -y dkms
    apt install -y hailo-all
    echo "Hailo installation complete."
else
    echo "Hailo HAT not detected. Skipping Hailo installation."
fi


### Node.js and npm
echo "[9/12] Installing Node.js and npm"
apt install -y nodejs npm


### Docker installation following this guide: https://docs.docker.com/engine/install/debian/
echo "[10/12] Installing Docker"
apt remove $(dpkg --get-selections docker.io docker-compose docker-doc podman-docker containerd runc | cut -f1)
# Add Docker's official GPG key:
apt update
apt install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo trixie) 
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt update

apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


#Joularcore installation (for energy monitoring)
echo "[11/12] installing joular core"
git clone https://github.com/joular/joularcore.git
cd joularcore
apt install rustup
rustup default stable
cargo build --release
cp target/release/joularcore /usr/local/bin/joularcore
cd ..
rm -rf joularcore




### Final Reboot
echo "[12/12] Installation process completed. Rebooting device to apply changes"
sleep 5
reboot
