# AudioMoth USB Microphone Update

This change switches the bird-call pipeline from our old USB mic to the
AudioMoth USB Microphone. Every changed line in the code has a comment that
starts with `AudioMoth update:` so you can find it quickly.

## What the AudioMoth firmware does

From `AudioMoth-USB-Microphone/src/main.c` and `inc/microphone.h`:

| Item | AudioMoth | Old code assumed |
| --- | --- | --- |
| USB device name | `<rate>kHz AudioMoth USB Microphone` (e.g. `384kHz AudioMoth USB Microphone`) | `USB Audio Device` |
| Sample rate | One fixed rate, set in the AudioMoth USB Microphone App. Default is 384000 Hz | 44100 Hz |
| Channels | 1 (mono) | 1 |
| Format | 16-bit PCM | n/a (sounddevice handles it) |

The mic only offers the one rate it is set to, so asking for 44100 Hz fails.
And because the name changed, our lookup would never find the mic: the reader
would just loop on `recording is None` forever without recording anything.

## Changes

### `audioReader.py`
- **Changed** `sampleRate` from `44100` to `384000` to match the AudioMoth's default rate.
- **Added** `micName = "AudioMoth USB Microphone"`, the name the mic reports over USB.
  It matches any rate, since the firmware puts the rate in front of the name.
- **Changed** the call to `fn.makeAudioFile(...)` to pass `micName` in.
- **Changed** the comment above `main()`: the mic is found by name, not device number.
- **Kept** everything else: `period`, `channelSelected = 1`, file names, folders,
  BirdNET settings, and the MQTT/CSV output (`MBC001`).

### `audioMints/functions.py`
- **Changed** `makeAudioFile(...)` to take a `deviceName` argument and pass it to
  `findUsbDevice(deviceName)`. Before, it always searched for `"USB Audio Device"`.
- **Kept** `findUsbDevice` itself and the rest of the file. `audioReader.py` is the only caller.

### `audioDeleter.py`
- **No change.** It only clears `/home/teamlary/mintsDataTmp` and
  `/home/teamlary/mintsDataJson`. Nothing in it depends on the microphone.

## Things to know

- **BirdNET still works at 384 kHz.** `audioMints/audio.py` loads the WAV with
  `librosa.load(..., sr=48000)`, which resamples to the 48 kHz BirdNET expects.
- **If you change the AudioMoth's sample rate** in the AudioMoth app, change
  `sampleRate` in `audioReader.py` to the same value (e.g. 48 kHz -> `48000`).
  `micName` does not need to change.
- **Bigger WAV files.** 9 s at 384 kHz is about 14 MB per recording (vs about 1.6 MB
  at 44.1 kHz). The reader overwrites the same `mintsAudio.wav` each cycle, so disk
  use does not grow, but resampling takes a bit more CPU each loop.
- **Not tested on hardware.** These changes come from reading the firmware source.
  To confirm on the Odroid, run `python3 -c "import sounddevice as sd; print(sd.query_devices())"`
  with the AudioMoth plugged in and check that it shows up with
  `AudioMoth USB Microphone` in its name.
