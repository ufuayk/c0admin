#!/bin/bash
set -e
INSTALL_DIR="$HOME/.c0admin"
EXECUTABLE_NAME="c0admin"
LAUNCHER_PATH="/usr/local/bin/$EXECUTABLE_NAME"
REPO_URL="https://github.com/ufuayk/c0admin.git"

echo "c0admin installation starting..."

echo "Installing system dependencies..."
sudo apt-get install -y python3-venv python3-pip 2>/dev/null || {
    echo "apt-get failed. Trying with sudo -S..."
    echo "Please enter your sudo password:"
    sudo -k apt-get install -y python3-venv python3-pip
}

if [ -d "$INSTALL_DIR" ]; then
   echo "Previous installation found. Removing..."
   rm -rf "$INSTALL_DIR"
fi

echo "Downloading GitHub repository..."
git clone "$REPO_URL" "$INSTALL_DIR"

echo "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

echo "Installing packages..."
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "Setting up $EXECUTABLE_NAME command..."
sudo bash -c "cat > $LAUNCHER_PATH" << EOF
#!/bin/bash
"$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/main.py"
EOF
sudo chmod +x "$LAUNCHER_PATH"

echo "Installation completed!"
echo "You can run the application by typing 'c0admin' in terminal."
