
# 🚀 Odroid N2+ Onboarding Guide

## 📥 OS Installation on SD Card  
1. Download the Odroid N2+ OS from [this link](https://wiki.odroid.com/odroid-n2/os_images/ubuntu/20220228).  
2. Use [Etcher](https://etcher.balena.io/) to flash the image onto your SD card.

---

## 👤 User Account Setup
1. Connect to the Odroid via a [UART Module](https://ameridroid.com/products/usb-uart-2-module-kit?pr_prod_strat=e5_desc&pr_rec_id=7b8882b26&pr_rec_pid=8013561757975&pr_ref_pid=69012291599&pr_seq=uniform).
2. Login using default credentials:
   - **Username:** `odroid`
   - **Password:** `odroid`
3. Create a new user:
   ```bash
   sudo adduser teamlary
   ```
4. Grant sudo privileges:
   ```bash
   sudo usermod -aG sudo teamlary
   ```
5. Switch to the new user:
   ```bash
   su teamlary
   ```
6. Create default directories:
   ```bash
   xdg-user-dirs-update
   ```
7. Verify sudo access:
   ```bash
   sudo whoami
   ```
   Expected output: `root`
8. Change the user password:
   ```bash
   passwd
   ```
9. Remove the default `odroid` user:
   ```bash
   sudo su
   userdel odroid
   userdel -r odroid
   ```

---

## 🕒 Time Zone & Clock Configuration

Ensure an RTC module is installed. Perform the following on all Linux-based MINTS nodes:

1. Check current time settings:
   ```bash
   timedatectl status
   ```
2. Set system time zone to UTC:
   ```bash
   timedatectl set-timezone UTC
   ```
3. Configure RTC to use UTC:
   ```bash
   timedatectl set-local-rtc 0
   ```
4. Enable NTP synchronization:
   ```bash
   timedatectl set-ntp true
   ```

✅ After completion, verify synchronization using:
```bash
timedatectl status
```

*Reference:* [Tecmint Guide](https://www.tecmint.com/set-time-timezone-and-synchronize-time-using-timedatectl-command/)

### 🌐 No Internet? Sync Time from RTC
If no internet is available, configure automatic RTC sync via `/etc/rc.local`:

1. Edit the file:
   ```bash
   sudo nano /etc/rc.local
   ```

2. Add the following script:

   ```bash
   #!/bin/bash

   if [ -f /aafirstboot ]; then 
       /aafirstboot start
   fi

   if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
       echo "$(date): Internet detected - Syncing system clock..."
       sudo systemctl restart systemd-timesyncd
       sleep 10

       if timedatectl | grep -q "System clock synchronized: yes"; then
           echo "$(date): Writing system time to RTC..."
           hwclock -w
       else
           echo "$(date): System clock not synced yet. Skipping RTC update." >> /var/log/time_sync.log
       fi
   else
       echo "No internet connection: Syncing system time from RTC..."
       hwclock -s
   fi

   exit 0
   ```

**Behavior:**
- 🌐 **With Internet:** Sync system clock via NTP and update RTC.
- 🚫 **Without Internet:** Restore system clock from RTC.

---

## 🌐 DWAgent Remote Access Setup

### 📥 Installation
1. On your DWService account, create a new agent.
2. Download the installer for Ubuntu:
   ```bash
   wget https://www.dwservice.net/download/dwagent.sh
   chmod +x dwagent.sh 
   sudo ./dwagent.sh
   ```
3. During installation, select **Installer Code** and enter the provided code to register the agent.
4. Complete the setup by copying the agent code to your system.

### ❌ Uninstallation
To remove DWAgent:
```bash
sudo bash /usr/share/dwagent/native/uninstall
```
Follow the on-screen instructions to complete the uninstallation.
