# Onboarding

## Getting the OS on the SD card  
- Download the Odroid OS for the N2+ from this [link](https://wiki.odroid.com/odroid-n2/os_images/ubuntu/20220228)
- Using [Etcher](https://etcher.balena.io/) get the image into an SD card.

## User Accounts
- Using a [UART Module](https://ameridroid.com/products/usb-uart-2-module-kit?pr_prod_strat=e5_desc&pr_rec_id=7b8882b26&pr_rec_pid=8013561757975&pr_ref_pid=69012291599&pr_seq=uniform) log into the odroid.
- The defaul credentials are given below
  - UN: odroid
  - PW: odroid
- Create user:
`sudo adduser teamlary` </br> 
- Provide sudo priviledges to the user: 
`sudo usermod -aG sudo teamlary`</br>
- Once the user is created, switch to the newly created user
`su teamlary`
- Check for attained priveledges:
` sudo whoami`</br>
The output should be `root`
- change password
` passwd `
- Delete the default user 
  - ```sudo su```
  - ```userdel odroid```
  - ```userdel -r odroid```

## Time Zone Set 

An RTC should be stup for this section. The instructions given below should be followed on all linux driven mints nodes:

- Veiw Time Zone Details:
```timedatectl  status```

- Set Time Zone to UTC Time: 
```timedatectl set-timezone UTC```

- Set Local (Real Time Clock) to UTC :
```timedatectl set-local-rtc 0```

- Sync with remote NTP(Network Time Protocol) server:
```timedatectl set-ntp true```

Afterwards `timedatectl  status` should give the following:
```
timedatectl  status
               Local time: Sat 2023-11-18 16:34:36 UTC
           Universal time: Sat 2023-11-18 16:34:36 UTC
                 RTC time: Sat 2023-11-18 16:34:36    
                Time zone: UTC (UTC, +0000)           
System clock synchronized: yes                        
              NTP service: active                     
          RTC in local TZ: no         

```
Derived using this [link](https://www.tecmint.com/set-time-timezone-and-synchronize-time-using-timedatectl-command/)
