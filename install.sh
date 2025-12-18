#!/bin/bash
# Installation script for CodeAtlas (Bash version)
# For systems where Python script might not work

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print header
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}🗺️  CodeAtlas Installation${NC}"
    echo ""
}

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Python not found! Please install Python 3.10+${NC}"
        exit 1
    fi
    
    VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo $VERSION | cut -d. -f1)
    MINOR=$(echo $VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        echo -e "${RED}❌ Python 3.10+ is required! Current: $VERSION${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python $VERSION detected${NC}"
}

# Detect package manager
detect_package_manager() {
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        echo -e "${RED}❌ pip not found! Please install pip${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Package manager detected: $PIP_CMD${NC}"
}

# Create virtual environment
create_venv() {
    VENV_PATH="${1:-venv}"
    
    if [ -d "$VENV_PATH" ]; then
        read -p "$(echo -e ${YELLOW}Virtual environment already exists. Recreate? [y/N]: ${NC})" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Removing existing virtual environment...${NC}"
            rm -rf "$VENV_PATH"
        else
            return 0
        fi
    fi
    
    echo -e "${CYAN}Creating virtual environment at $VENV_PATH...${NC}"
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo -e "${GREEN}✅ Virtual environment created successfully${NC}"
}

# Install dependencies
install_dependencies() {
    VENV_PATH="$1"
    PROJECT_PATH="$2"
    USE_DEV="$3"
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        PIP="$VENV_PATH/Scripts/pip"
        PYTHON="$VENV_PATH/Scripts/python"
    else
        PIP="$VENV_PATH/bin/pip"
        PYTHON="$VENV_PATH/bin/python"
    fi
    
    echo -e "${CYAN}Upgrading pip...${NC}"
    $PIP install --upgrade pip wheel setuptools --quiet
    
    echo -e "${CYAN}Installing CodeAtlas...${NC}"
    if [ "$USE_DEV" = "true" ]; then
        $PIP install -e ".[dev]" --quiet
    else
        $PIP install -e . --quiet
    fi
    
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
}

# Install optional tools
install_optional_tools() {
    VENV_PATH="$1"
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        PIP="$VENV_PATH/Scripts/pip"
    else
        PIP="$VENV_PATH/bin/pip"
    fi
    
    read -p "$(echo -e ${YELLOW}Install optional security tools? (bandit, safety, pip-audit) [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Installing optional tools...${NC}"
        $PIP install bandit safety pip-audit pip-licenses --quiet
        echo -e "${GREEN}✅ Optional tools installed${NC}"
    fi
}

# Verify installation
verify_installation() {
    VENV_PATH="$1"
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        CODEATLAS="$VENV_PATH/Scripts/codeatlas"
    else
        CODEATLAS="$VENV_PATH/bin/codeatlas"
    fi
    
    echo -e "${CYAN}Verifying installation...${NC}"
    if $CODEATLAS version &> /dev/null; then
        echo -e "${GREEN}✅ Installation verified successfully!${NC}"
        $CODEATLAS version
    else
        echo -e "${YELLOW}⚠️  Verification failed, but installation may still be successful${NC}"
    fi
}

# Show usage instructions
show_usage() {
    VENV_PATH="$1"
    
    echo ""
    echo -e "${GREEN}${BOLD}✅ Installation Complete!${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}🚀 Getting Started:${NC}"
    echo ""
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo -e "${BOLD}1. Activate the virtual environment:${NC}"
        echo -e "   ${YELLOW}$VENV_PATH\\Scripts\\activate${NC}"
        echo ""
        echo -e "${BOLD}2. Run CodeAtlas:${NC}"
        echo -e "   ${YELLOW}codeatlas --help${NC}"
        echo -e "   ${YELLOW}codeatlas scan .${NC}"
    else
        echo -e "${BOLD}1. Activate the virtual environment:${NC}"
        echo -e "   ${YELLOW}source $VENV_PATH/bin/activate${NC}"
        echo ""
        echo -e "${BOLD}2. Run CodeAtlas:${NC}"
        echo -e "   ${YELLOW}codeatlas --help${NC}"
        echo -e "   ${YELLOW}codeatlas scan .${NC}"
    fi
    echo ""
}

# Find virtual environments
find_venvs() {
    PROJECT_PATH="$1"
    VENVS=()
    
    # Check common locations
    for venv_name in "venv" ".venv" "env"; do
        VENV_PATH="$PROJECT_PATH/$venv_name"
        if [ -d "$VENV_PATH" ]; then
            # Check if it's actually a venv
            if [ -f "$VENV_PATH/bin/python" ] || [ -f "$VENV_PATH/Scripts/python.exe" ]; then
                VENVS+=("$VENV_PATH")
            fi
        fi
    done
    
    # Check home directory
    HOME_VENV="$HOME/.codeatlas/venv"
    if [ -d "$HOME_VENV" ]; then
        if [ -f "$HOME_VENV/bin/python" ] || [ -f "$HOME_VENV/Scripts/python.exe" ]; then
            VENVS+=("$HOME_VENV")
        fi
    fi
    
    echo "${VENVS[@]}"
}

# Uninstall CodeAtlas
uninstall() {
    PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REMOVE_CONFIG="${1:-false}"
    
    echo ""
    echo -e "${RED}${BOLD}🗑️  CodeAtlas Uninstall${NC}"
    echo ""
    
    # Find virtual environments
    VENVS=($(find_venvs "$PROJECT_PATH"))
    
    if [ ${#VENVS[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No virtual environment found to uninstall${NC}"
        return 1
    fi
    
    # Select venv if multiple
    if [ ${#VENVS[@]} -eq 1 ]; then
        VENV_PATH="${VENVS[0]}"
        echo -e "${CYAN}Found virtual environment: $VENV_PATH${NC}"
    else
        echo -e "${YELLOW}Multiple virtual environments found:${NC}"
        for i in "${!VENVS[@]}"; do
            echo -e "  $((i+1)). ${VENVS[i]}"
        done
        read -p "$(echo -e ${CYAN}Select virtual environment to remove (number): ${NC})" CHOICE
        CHOICE=$((CHOICE-1))
        if [ $CHOICE -ge 0 ] && [ $CHOICE -lt ${#VENVS[@]} ]; then
            VENV_PATH="${VENVS[$CHOICE]}"
        else
            echo -e "${RED}❌ Invalid selection${NC}"
            return 1
        fi
    fi
    
    # Confirm removal
    read -p "$(echo -e ${RED}${BOLD}⚠️  Remove virtual environment at $VENV_PATH? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Uninstall cancelled${NC}"
        return 1
    fi
    
    # Remove virtual environment
    echo -e "${CYAN}Removing virtual environment...${NC}"
    rm -rf "$VENV_PATH"
    echo -e "${GREEN}✅ Virtual environment removed successfully${NC}"
    
    # Remove config if requested
    if [ "$REMOVE_CONFIG" = "true" ]; then
        CONFIG_PATHS=(
            "$PROJECT_PATH/.codeatlas"
            "$HOME/.config/CodeAtlas"
        )
        
        for config_path in "${CONFIG_PATHS[@]}"; do
            if [ -e "$config_path" ]; then
                rm -rf "$config_path"
                echo -e "${GREEN}✅ Removed config: $config_path${NC}"
            fi
        done
    fi
    
    echo ""
    echo -e "${GREEN}${BOLD}✅ CodeAtlas has been uninstalled successfully!${NC}"
    echo -e "${CYAN}All virtual environment files have been removed.${NC}"
    echo ""
}

# Main installation
main() {
    print_header
    
    # Get project directory
    PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${CYAN}Project path: $PROJECT_PATH${NC}"
    echo ""
    
    # Check Python
    check_python
    
    # Detect package manager
    detect_package_manager
    
    echo ""
    
    # Ask for venv location
    read -p "$(echo -e ${CYAN}Virtual environment location [venv]: ${NC})" VENV_LOCATION
    VENV_PATH="${VENV_LOCATION:-venv}"
    VENV_PATH="$(cd "$(dirname "$VENV_PATH")" && pwd)/$(basename "$VENV_PATH")"
    
    # Ask for dev dependencies
    read -p "$(echo -e ${YELLOW}Install development dependencies? [y/N]: ${NC})" -n 1 -r
    echo
    USE_DEV="false"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USE_DEV="true"
    fi
    
    echo ""
    
    # Create venv
    create_venv "$VENV_PATH"
    
    echo ""
    
    # Install dependencies
    install_dependencies "$VENV_PATH" "$PROJECT_PATH" "$USE_DEV"
    
    echo ""
    
    # Install optional tools
    install_optional_tools "$VENV_PATH"
    
    echo ""
    
    # Verify
    verify_installation "$VENV_PATH"
    
    # Show usage
    show_usage "$VENV_PATH"
}

# Check for uninstall flag
if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
    REMOVE_CONFIG="false"
    if [ "$2" = "--remove-config" ]; then
        REMOVE_CONFIG="true"
    fi
    uninstall "$REMOVE_CONFIG"
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "CodeAtlas Installation Script"
    echo ""
    echo "Usage:"
    echo "  ./install.sh              Install CodeAtlas"
    echo "  ./install.sh --uninstall  Uninstall CodeAtlas"
    echo "  ./install.sh --uninstall --remove-config  Uninstall and remove config"
    echo ""
else
    # Run main
    main "$@"
fi

