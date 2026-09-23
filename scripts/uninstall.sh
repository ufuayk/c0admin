#!/bin/bash

INSTALL_DIR="$HOME/.c0admin"
EXECUTABLE_PATH="/usr/local/bin/c0admin"

echo "This will completely remove c0admin from your system."
read -p "Are you sure you want to continue? (y/n): " confirm

if [[ "$confirm" != "y" ]]; then
    echo "Uninstallation cancelled."
    exit 1
fi
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
else
    echo "Installation directory not found."
fi

if [ -f "$EXECUTABLE_PATH" ]; then
    echo "Removing $EXECUTABLE_PATH..."
    sudo rm -f "$EXECUTABLE_PATH"
else
    echo "Global command not found."
fi

echo "c0admin has been uninstalled successfully."
