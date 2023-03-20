# Private/Public key conversion from SSH2 to OpenSSH:
ssh-keygen -i -f path/to/id_rsa > path/to/openssh.prv
ssh-keygen -i -f path/to/id_rsa.pub > path/to/openssh.pub

# Key conversion from SSH2 to OpenSSH with key format:
ssh-keygen -i -f path/to/id_rsa.pub -m PKCS8 > path/to/openssh.pub

# Calculate public key fingerprint
ssh-keygen -l -f path/to/openssh.pub

# Private/Public key conversion from OpenSSH to SSH2:
# Default: -m RFC4716
ssh-keygen -e -f path/to/openssh.prv > path/to/id_rsa
ssh-keygen -e -f path/to/openssh.pub > path/to/id_rsa.pub
