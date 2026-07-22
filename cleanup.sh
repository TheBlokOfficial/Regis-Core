#!/bin/bash
sudo sed -i '/^\[NAS\]/,$d' /etc/samba/smb.conf
sudo smbpasswd -x theblok || true
sudo systemctl restart smbd
