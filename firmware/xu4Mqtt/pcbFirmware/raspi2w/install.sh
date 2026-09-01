if [ -d "./.venv" ]; then
    echo "Removing existing .venv virtual environment. Starting in 10 seconds"
    sleep 10
    rm -rf ./.venv
fi

python3 -m venv .venv
source .venv/bin/activate
pip install smbus2 pyserial paho-mqtt pyyaml getmac pynmea2 netifaces pandas joblib RPi.bme280