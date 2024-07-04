#!/bin/bash

# Prompt for username
read -p "Enter the new username: " USERNAME

# Check if username is empty
if [ -z "$USERNAME" ]; then
    echo "Error: Username cannot be empty."
    exit 1
fi

# Create the user
useradd -m -s /bin/bash $USERNAME

# Set a password
passwd $USERNAME

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
usermod -aG sudo $USERNAME

# Verify the user was created
id $USERNAME

echo "User $USERNAME has been created successfully."
