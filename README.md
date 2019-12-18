## This is an Open-Source Ninebot and Xiaomi compatible scooter interface app.

### **THIS TOOL IS ONLY FOR USE ON DEVICES YOU OWN!!!** It is still being added to but is in a functional state.


This application is written in Python3. To install required libraries, run the following two commands:

```bash
git clone --recursive https://github.com/slinger360/NineRiFt-kivy.git
pip install -r requirements.txt
```

To build for Android read up on `Buildozer`.

After that, you can either run NineRiFt on your `Windows`, `Mac`, or `Linux` machine by opening `main.py` using your Python3 interpreter or you can use a prebuilt APK for Android (you could also compile a build if you want).

On Android, BLE and TCP-Serial is supported.

On, Windows, Mac, and Linux, BLE, Serial, and TCP is supported.


## The Download screen is for downloading firmware:

1. Select device you need firmware for in the dropdown on the left

2. Select the firmware version you need

3. Click "Download it!" and wait for download to complete


## The Flash screen is for flashing firmware:

1. (Optional) Type the first few digits or the full length of the MAC address of the target scooter for flashing

2. Select the interface you want to use to connect (if wired, plug it in first)

3. Select the part you wish to flash

4. Select the firmware file you want flashed to the target scooter. DO NOT SELECT AN MD5 FILE!!! THIS IS NOT THE FIRMWARE!!!

5. Click "Flash it!" and wait for flashing to complete



At the moment only Segway-Ninebot SNSC, ES1, ES2, and ES4 and Xiaomi M365 and M365 Pro are supported.


SNSC dashboards cannot be flashed without either TCP-Serial or Serial interface.



If you appreciate my work, be sure to donate at https://PayPal.com/dilsha21 or any of the other options listed on my GitHub.
