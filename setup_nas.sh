#!/bin/bash
sudo sed -i '/^\[NAS\]/,$d' /etc/samba/smb.conf

sudo tee -a /etc/samba/smb.conf > /dev/null <<EOT

[NAS]
   path = /home/theblok/NAS
   writeable = yes
   create mask = 0775
   directory mask = 0775
   public = no
   valid users = theblok
EOT

(echo "nas123"; echo "nas123") | sudo smbpasswd -s -a theblok
sudo systemctl restart smbd
