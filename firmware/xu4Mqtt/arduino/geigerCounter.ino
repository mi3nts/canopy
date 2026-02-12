/*!
  @file geiger.ino
  @brief    Detect CPM radiation intensity, the readings may have a large deviation at first, and the data tends to be stable after 3 times
  @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @licence     The MIT License (MIT)
  @author [fengli](li.feng@dfrobot.com)
  @version  V1.0
  @date  2021-9-17
  @get from https://www.dfrobot.com
  @https://github.com/DFRobot/DFRobot_Geiger
*/

#include <DFRobot_Geiger.h>
#if defined ESP32
#define detect_pin D10
#else
#define detect_pin 10
#endif
/*!
   @brief Constructor
   @param pin   External interrupt pin
*/
DFRobot_Geiger  geiger(detect_pin);

void setup()
{
  Serial.begin(115200);
  //Start counting, enable external interrupt
  geiger.start();
}

void loop() {
  //Start counting, enable external interrupt
  //geiger.start();
  delay(3000);
  //Pause the count, turn off the external interrupt trigger, the CPM and radiation intensity values remain in the state before the pause
  //geiger.pause();
  //Get the current CPM, if it has been paused, the CPM is the last value before the pause
  //Predict CPM by falling edge pulse within 3 seconds, the error is ±3CPM
  Serial.print("CPM: ");
  Serial.println(geiger.getCPM());
  //Get the current nSv/h, if it has been paused, nSv/h is the last value before the pause
  Serial.print("nSv/h: ");
  Serial.println(geiger.getnSvh());
  //Get the current μSv/h, if it has been paused, the μSv/h is the last value before the pause
  Serial.print("uSv/h: ");
  Serial.println(geiger.getuSvh());
}
