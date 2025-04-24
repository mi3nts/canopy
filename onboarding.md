
# Onboarding Guide

## 📥 Getting the OS on the SD Card  
1. Download the Odroid OS for the N2+ from this [link](https://wiki.odroid.com/odroid-n2/os_images/ubuntu/20220228).  
2. Use [Etcher](https://etcher.balena.io/) to flash the image onto an SD card.

---

## 👤 User Accounts Setup
1. Connect to the Odroid using a [UART Module](https://ameridroid.com/products/usb-uart-2-module-kit?pr_prod_strat=e5_desc&pr_rec_id=7b8882b26&pr_rec_pid=8013561757975&pr_ref_pid=69012291599&pr_seq=uniform).
2. Default credentials:
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
6. Create default folders:
   ```bash
   xdg-user-dirs-update
   ```   
7. Verify sudo privileges:
   ```bash
   sudo whoami
   ```
   Output should be `root`.
8. Change password:
   ```bash
   passwd
   ```
9. Delete the default user:
   ```bash
   sudo su
   userdel odroid
   userdel -r odroid
   ```

---

## 🕒 Time Zone Configuration

Ensure an RTC module is installed. Follow these steps on all Linux-based MINTS nodes:

1. View current time settings:
   ```bash
   timedatectl status
   ```
2. Set time zone to UTC:
   ```bash
   timedatectl set-timezone UTC
   ```
3. Set RTC to UTC:
   ```bash
   timedatectl set-local-rtc 0
   ```
4. Enable NTP synchronization:
   ```bash
   timedatectl set-ntp true
   ```

After setup, `timedatectl status` should display synchronized UTC time.  
Reference: [Tecmint Guide](https://www.tecmint.com/set-time-timezone-and-synchronize-time-using-timedatectl-command/)

### Handling No Internet Scenarios
If internet is unavailable, configure the system to sync time from the RTC by updating `/etc/rc.local`:

Edit using:
```bash
sudo nano /etc/rc.local
```

Add the following content:

```bash
#!/bin/bash

# Run first boot script if exists
if [ -f /aafirstboot ]; then 
    /aafirstboot start
fi

# Check for internet connection
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

This ensures:
- **With Internet:** System clock syncs via NTP and updates the RTC (`hwclock -w`).
- **Without Internet:** System clock is restored from the RTC (`hwclock -s`).
