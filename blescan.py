import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
from bluepy.btle import Scanner, DefaultDelegate
from datetime import datetime
import RPi.GPIO as GPIO

# LED Setting
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED = 11
GPIO.setup(LED, GPIO.OUT)

# firebase certificate&init
cred = credentials.Certificate("/home/serviceAccountKey.json")
#'database url'
firebase_admin.initialize_app(cred,{'databaseURL' : 'https://test-energizor-default-rtdb.firebaseio.com'})

# new empty object
firebaseMacSet = set()
BLEScanMacSet = set()
matchedMacSet = set()
matchedMacList = []

while True:

    # clear
    firebaseMacSet.clear()
    BLEScanMacSet.clear()
    matchedMacSet.clear()
    matchedMacList.clear()

    # json-> object
    # Mac value List from.firebase 
    ref = db.reference().child("DataSet")
    snapshot = ref.get()
    for key in snapshot:
        firebaseResult = ref.child(key).child("Beacon").child("BeaconMAC")
        firebaseMacSet.add(firebaseResult.get())
        
    # BLEScan
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)        
            def handleDiscovery(self, dev, isNewDev, isNewData):
                if isNewDev:
                    print("Discovered device %s "% dev.addr)
                elif isNewData:
                    print("Received new data from %s", dev.addr)
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(30.0) # setting scan time - 30s

    # dev.addr = MAC
    # dev.addrType = if(public) -> fixed value
    for dev in devices:
        #trans capital
        devAddr = dev.addr
        BLEScanMacSet.add(devAddr.upper())

    # firebaseMAC match with BLEScanMaC
    matchedMacSet.update(firebaseMacSet & BLEScanMacSet)

    # LED on/off
    if len(matchedMacSet) > 0:
        GPIO.output(LED, GPIO.HIGH) #ON
    else:
        GPIO.output(LED, GPIO.LOW) #OFF

    # indexing, finding firebase
    matchedMacList = list(matchedMacSet)
    for idx in range(len(matchedMacList)):
        for key in snapshot:
            firebaseResult = ref.child(key).child("Beacon").child("BeaconMAC")
            if matchedMacList[idx] == firebaseResult.get():
                # send DeviceNo, location and time to firebase
                now = datetime.now() #current time
                ref.child(key).child("TrafficLight").child("Scan").update({"DeviceNo" : 58, "latitude": 36.14337, "longitude": 128.39334})
                ref.child(key).child("TrafficLight").child("Scan").child("Time").set(now.strftime('%Y-%m-%d %H:%M:%S'))
        
        #print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))   
        #for(adtype, desc, value) in dev.getScanData():
            #print(" %s = %s" % (desc, value))
