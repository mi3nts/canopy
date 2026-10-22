#from importlib_metadata import files

from scipy.io.wavfile import write
import os

import csv

import sys
from collections import OrderedDict
import datetime

import numpy as np
import pandas as pd

import time

time.sleep(1) 

from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions as mD

from multiprocessing import Pool, freeze_support
from audioMints import config as cfg
from audioMints import functions as fn

# AudioMoth update: the AudioMoth only streams at the rate set in the AudioMoth
# USB Microphone App (default 384kHz). Asking for any other rate (old value was
# 44100) fails. BirdNET resamples to 48kHz on its own, so detection is unchanged.
sampleRate         = 384000  # Sample rate (must match the AudioMoth's setting)
period             = 9 # Duration of recording
channelSelected    = 1 # AudioMoth is mono, so 1 channel stays the same
micName            = "AudioMoth USB Microphone" # AudioMoth update: name the mic reports over USB
audioFileNamePre   = "mintsAudio"
tmpFolderName      = "/home/teamlary/NC/"
minConfidence      = .3
numOfThreads       = 4

dataFolder         = mD.dataFolder


currentIndex = 0

# AudioMoth update: the mic is found by name (micName above), not device number.
# If it is not found, check the name it shows up with by running
# import sounddevice as sd
# print(sd.query_devices())
# in a live python terminal

def main(cfg,currentIndex):
    labels = pd.read_csv("audioMints/labels/labels.csv") 
    mSR.directoryCheck(tmpFolderName)

    while True:
        try:
            dateTime = datetime.datetime.now()
            # AudioMoth update: micName is passed in so the AudioMoth is the device we record from
            recording = fn.makeAudioFile(sampleRate,period,channelSelected,audioFileNamePre+ ".wav",tmpFolderName,micName)
            if recording is None:
                time.sleep(1)
                continue
            
            # Freeze support for executable
            freeze_support()
            cfg = fn.configSetUp(cfg,tmpFolderName,minConfidence,numOfThreads)
            soundClassData = pd.read_csv(tmpFolderName + '/'+ audioFileNamePre +  '.BirdNET.results.csv')
            soundClassData["Labels"] = soundClassData["Scientific name"].map(labels.set_index("Scientific name")["Labels"])
            print(soundClassData)
            for index, row in soundClassData.iterrows():
                sensorDictionary = OrderedDict([
                    ("dateTime"     ,str(dateTime + datetime.timedelta(seconds = row['Start (s)']))),
                    ("label"        ,row['Labels']),
                    ("confidence"   ,row['Confidence'])
                     ])
                mSR.sensorFinisher(dateTime,"MBC001",sensorDictionary)

            print("=============")
            print()

        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
            print("Microphone Not Connected: Check connection")
            

if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print("Connecting to the microphone on Channel: {0}".format(channelSelected) + " with Sample Rate " + str(sampleRate))
    main(cfg,currentIndex)    