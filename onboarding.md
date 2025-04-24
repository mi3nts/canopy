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
`su - teamlary`
- Check for attained priveledges:
` sudo whoami`</br>
The output should be `root`
- change password
` passwd `
- Delete the default user 
  - ```sudo su -```
  - ```userdel odroid```
  - ```userdel -r odroid```
