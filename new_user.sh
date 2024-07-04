#!/bin/bash

# Check if username is provided as an argument
if [ $# -eq 0 ]; then
    echo "Error: Please provide a username."
    echo "Usage: curl -s https://your-repo-url/script.sh | bash -s username"
    exit 1
fi

USERNAME=$1

# Create the user
useradd -m -s /bin/bash $USERNAME

# Generate a random password
PASSWORD=$(openssl rand -base64 12)

# Set the password
echo "$USERNAME:$PASSWORD" | chpasswd

# Create the home directory if it doesn't exist
mkdir -p /home/$USERNAME

# Set ownership
chown $USERNAME:$USERNAME /home/$USERNAME

# Set permissions
chmod 700 /home/$USERNAME

# Copy default config files
cp -R /etc/skel/. /home/$USERNAME

# Optional: Add user to sudo group
# Uncomment the next line to enable
# usermod -aG sudo $USERNAME

# Verify the user was created
id $USERNAME

echo "User $USERNAME has been created successfully."
echo "Generated password: $PASSWORD"
echo "Please change this password upon first login."
