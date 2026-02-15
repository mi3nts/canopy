#include <Wire.h>
#include <multi_channel_relay.h>


// NOTES
// We made some minor changes to multi_channel_relay.cpp's scanI2CDevices() function
// It is not used here but if you find it crashes the arduino, use that and it might fix it
// TODO: 
// include LoRaWAN node support (should be easy, but not testable yet)


Multi_Channel_Relay relay;

const unsigned long TIMEOUT_MS = 10000;    
const unsigned long RESET_TIME_MS = 2000;  
const unsigned long BOOT_GRACE_MS = 60000; 

struct OdroidMonitor {
  uint8_t pin;              
  uint8_t relayChannelBit;  
  int lastPinState;         
  unsigned long lastPulseTime; // Timestamp of last state change
  bool isRecovering;        // currently booting up?
  unsigned long recoveryStartTime;
};


// NOTE: the relay uses one-hot encoding; i.e. channel1 = 0001/0x01, channel2 = 0010 / 0x02, channel3 = 0100 / 0x04, channel4 = 1000 / 0x08
OdroidMonitor odroid1 = {7,  0x04, LOW, 0, true, 0}; 
OdroidMonitor odroid2 = {15, 0x02, LOW, 0, true, 0};

void setup() {
  Serial.begin(9600);
  while(!Serial);

  pinMode(odroid1.pin, INPUT);
  pinMode(odroid2.pin, INPUT);

  relay.begin(0x11); 
  
  // Turn ON both channels initially
  relay.channelCtrl(odroid1.relayChannelBit | odroid2.relayChannelBit);
  Serial.println("System Monitor Started. Relays ON.");
  
  unsigned long now = millis();
  odroid1.recoveryStartTime = now;
  odroid2.recoveryStartTime = now;
}

void loop() {
  checkAndReset(odroid1, "ODROID 1");
  checkAndReset(odroid2, "ODROID 2");
  
  delay(10); 
}

void checkAndReset(OdroidMonitor &mon, String name) {
  unsigned long currentMillis = millis();

  if (mon.isRecovering) {
    if (currentMillis - mon.recoveryStartTime > BOOT_GRACE_MS) {
      mon.isRecovering = false;
      mon.lastPulseTime = currentMillis; // reset timer so it doesn't fail immediately
      Serial.print(name);
      Serial.println(" grace period ended. Monitoring active.");
    }
    return; // Don't check pulses while recovering
  }
  int currentState = digitalRead(mon.pin);

  if (currentState != mon.lastPinState) {
    mon.lastPulseTime = currentMillis; 
    mon.lastPinState = currentState;
  }

  if (currentMillis - mon.lastPulseTime > TIMEOUT_MS) {
    Serial.print("CRITICAL: ");
    Serial.print(name);
    Serial.println(" heartbeat lost! Initiating Reset...");

    performReset(mon);
  }
}

void performReset(OdroidMonitor &mon) {
  relay.turn_off_channel(_getChannelNumber(mon.relayChannelBit)); 
  
  Serial.println("Power CUT");
  delay(RESET_TIME_MS); 
  
  relay.turn_on_channel(_getChannelNumber(mon.relayChannelBit));
  Serial.println("Power RESTORED");

  mon.isRecovering = true;
  mon.recoveryStartTime = millis();
  mon.lastPulseTime = millis();
  mon.lastPinState = digitalRead(mon.pin);
}

// need to use a helper function as the relay channel uses one-hot
int _getChannelNumber(uint8_t bitmask) {
  if (bitmask == 0x01) return 1;
  if (bitmask == 0x02) return 2;
  if (bitmask == 0x04) return 3;
  if (bitmask == 0x08) return 4;
  return 1;
}