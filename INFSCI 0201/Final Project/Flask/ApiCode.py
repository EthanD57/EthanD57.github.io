import json
from flask import Flask, render_template, request
from model.smartDevices import Thermostat, LightBulb, SmartVacuum, SmartPlug, SmartLock, Home, SmartDevice
import requests


app = Flask(__name__)

home = Home("135 N Bellefield Ave")

@app.route("/")
def index():
    if home._smart_devices:
        return render_template("home.html", home=home)
    else:
        try:
            load_home()
        except:
            pass
    return render_template("home.html", home=home)


@app.route('/add-device', methods=['POST'])
def add():
    attributes = request.get_json()              

    if "temperature" in attributes:
        device = Thermostat(attributes["name"], attributes["manufacturer"], attributes["temperature"])
    elif "brightness" in attributes:
        device = LightBulb(attributes["name"], attributes["manufacturer"], attributes["brightness"])
    elif "cleaning" in attributes:
        device = SmartVacuum(attributes["name"], attributes["manufacturer"], attributes["cleaning"])
    elif "state" in attributes:
        device = SmartPlug(attributes["name"], attributes["manufacturer"], attributes["state"])
    elif "locked" in attributes:
        device = SmartLock(attributes["name"], attributes["manufacturer"], attributes["locked"])
    else:
        print("Invalid device! Check driver code for valid devices.")
        return render_template("home.html", home=home)
    home.add_device(device)

    print(device._name + " added to " + home._address)

    return render_template("home.html", home=home)

@app.route('/<device_name>/<method_name>/<input>', methods=['PUT'])
def call(device_name, method_name, input):
    device_name = device_name.replace("_", " ")  # Replace underscores with spaces
    device = home.get_device(device_name)
    method = getattr(device, method_name)
    method(input)
    return render_template("home.html", home=home)

@app.route('/save', methods=['POST'])
def save_home():
    devices_dict = {
        device._name: {k.lstrip('_'): v for k, v in device.__dict__.items()} 
        for device in home._smart_devices
    }
    with open('home.json', 'w') as f:
        json.dump(devices_dict, f)
    return "Home saved", 200

@app.route('/delete/<name>', methods=['DELETE'])
def delete(name):
    home._smart_devices = [device for device in home._smart_devices if device._name != name]
    return render_template("home.html", home=home)

@app.route('/load', methods=['GET'])
def load_home():
    global home
    with open('home.json', 'r') as f:
        devices_dict = json.load(f)
    for name, device_dict in devices_dict.items():
        if "temperature" in device_dict:
            device = Thermostat(**device_dict)
        elif "brightness" in device_dict:
            device = LightBulb(**device_dict)
        elif "cleaning" in device_dict:
            device = SmartVacuum(**device_dict)
        elif "state" in device_dict:
            device = SmartPlug(**device_dict)
        elif "locked" in device_dict:
            device = SmartLock(**device_dict)
        else:
            print("Invalid device! Check driver code for valid devices.")
            return render_template("home.html", home=home)
        home.add_device(device)
    return "Home loaded", 200

@app.route('/temperatureDifference/<zip>', methods=['GET'])
def tempDiff(zip):
    url = "http://api.weatherstack.com/current"
    access_key = "ea31b1e93ebfb5007496a6974d55e072" # Note: This is NOT a secure way of doing this
    query = str(zip)
    units = "f"
    response = requests.get(url, params={"access_key": access_key, "query": query, "units": units})
    response = response.json()
    current_temp = response["current"]["temperature"]
    temp_diff = current_temp - home._smart_devices[0]._temperature
    return str(temp_diff), 200

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)