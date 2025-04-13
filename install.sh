#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"

                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                          .:--::       .-+*&#@░▒▒▒▒▒▒░░@#%*=:.      .:--:.                          
                       .+%@@#&**&*++%@▒▓░#%+=-:..#@-..:-=*%@▒▓▒#**=%%+%&#@@%:                       
                      :@▓█████▓█##*&&%-        .&=:*=   .    .+&#*@@▒███████▓*                      
                      #█▒*==&██████#%%*%.+░.&+:&#▒▓&%#*%▓-#=+**&#▒█████░*==&██-                     
                      @▓..=@█#=*▒███▓▓█#%▓████@@████▓*█████░%@▓▒████#=%▒▒%. *█=                     
                      -*+▒▓%.   .%█████░░@░██@@█▓▓▒▒▓▓&██▓#&@▒████▒:    =@█&-&                      
                      =░▓*.  .@%..▒█████▒@░@█▒▓▓▓#*██▓▒▓▒@@@███████-..    -@█%.                     
                    .#█&.   +&██▓▓███████▓▒█████#▒▒#░███▓▒░████████▓░░:     =▒▒-                    
                   -▒▒-   =*███▓██████████████▒▒▒▒▒▒▒▒▒███████████████##*    .&█*                   
                  =█@.   -▓██████████@█████▒▒▓█████████▒▒▓████░▓█████████&.    +█#.                 
                 =█#.   .░██████████@▓██▓▒▓█████@░&░▒█████▒▓███#▒████████▓▓=    =█@.                
                -█@.   +███████░#%+--▓█░▓████▓#-.   :=░█████▒▓█@:=*%#▒█████▓:    +█%                
               .░▓.   +▓▓▒▒@#&#@#%+&██░██▓░░█░..:-::: :▓▒▒▒███▓█░**&#@&#@░▒▒▓=    &█-               
               +█+   .%██▓▒▓█████████▒██#%. =▒@#%=+:%#░@. -&░██▒█████████▒▒██▓.   .▓░               
               ▒▒    :░██▒@#░▒▓██▓#█▒███▓@░%=&█*.   .░░==%░▒████▓▓░██▓▓▒@@@▓██%    %█=              
              -█&    +▓▓%#▒███████▒▒█████@▒▓+.░*    .@&.&█░░█████▒███████░&%██░:   :█#              
              +█+   .#████▓@##@▓█▓▒██████████:▒+    .+*&██████████▒██░###▒█████=    ▓░              
              %█-  :▒██████████░@▒███████████*:..   .:.░███████████░@▓█████████▒:   ▒▓              
              *█-   #███████████░████████▓&██&.      ..░█▒@█████████▒██████████&.   ▒▒              
              =█+  :▓██████████░██████████@=██::     :+█░-▓█████████▒▓█████████░:  .█@              
              .█#  -@██████████▒███████████▓▓&.░&*=%@&.▓▓████████████░█████████@.  =█%              
               #█. .@██████████░█████████████* .+#▒&- .▒████████████▓▓█████████░:  #█:              
               -█& .%███████████▒████████████▓%++&@*+%@█████████████▒██████████@- -█&               
                &█=.#████████▒███▓████████████▓%&▓█@%#█████████████▓██▓▓███████░-.▒▒.               
                .░▓=▓███████▓██████████████████████████▒███████████████▓▓██████▓+@█-                
                 :▒▓░███▓▓▓███████████████████░▓█████▓███████████████████▓▓▓███▒░█=                 
                  .@██▒▓███████████████████████@#▓██░████████████████████████▓▒█▓-                  
                   .@▒▒▒████████████████████████▒@▒@▓▓████████████████████████▓▒-                   
                   +▒███▒██████▓██████████████████#█▓▓██████████████▓██████▒▒███@.                  
                  -▒█████████████████████████████&█████████████████████████▓█████#.                 
                 .▒█████████████@████████████████#▒███████████████████████████████+                 
                 -███████████████████████████████▒▓███████████████████████████████@                 
                 -░▓█████████████████████████████████████████████████████████████▓&                 
                  = #░████████████████████████████████████████████████████████▓&%=                  
                    =+:+░██████████████████████████████████████████████████░░:+ +                   
                     -.:--@#▓██████████████████████████████████████████▓▒%&.* -                     
                       :- * =*&▒▒██████████████████████████████████▓█&&:= = +                       
                          *  ..%.+░▓████████████████████████████▓░▒.+..   =                         
                          *    * .%+=##██████████████████████▓*@.*+ +     =                         
                          :    +  =+:+.+*@▓░████████████▓▒@&%- + *- +.    :                         
                                  :=.= .-*:.=&%░█▓▓▒▓#&%:..*-  + *                                  
                                  ...=  .-   .. =...- .    -   + .                                  
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    


Prompt Assisted Workflow
EOF
echo -e "${NC}"

echo -e "${GREEN}[*] Installing PAW - Prompt Assisted Workflow...${NC}"

# Check if running on Kali Linux
if ! grep -q 'Kali' /etc/os-release; then
    echo -e "${YELLOW}[!] Warning: This script is designed for Kali Linux. Results on other distributions may vary.${NC}"
fi

# Create installation directories
echo -e "${BLUE}[*] Creating installation directories...${NC}"
INSTALL_DIR="/usr/local/share/paw"
CONFIG_DIR="/etc/paw"
LOG_DIR="/var/log/paw"

# Create directories
sudo mkdir -p ${INSTALL_DIR}/{bin,lib,tools,custom_commands}
sudo mkdir -p ${CONFIG_DIR}
sudo mkdir -p ${LOG_DIR}

# Install Python dependencies
echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
pip install requests openai python-dotenv rich httpx

# Install Ollama
echo -e "${BLUE}[*] Installing Ollama...${NC}"
curl -fsSL https://ollama.com/install.sh | sh

# Wait for Ollama to start
echo -e "${BLUE}[*] Starting Ollama service...${NC}"
sleep 2

# Pull the required model
echo -e "${BLUE}[*] Downloading LLM model (this may take a while)...${NC}"
ollama pull MartinRizzo/Ayla-Light-v2:12b-q4_K_M

# Set executable permissions for Python files
echo -e "${BLUE}[*] Setting executable permissions...${NC}"
chmod +x paw.py ascii_art.py tools_registry.py add_custom_tool.py
chmod +x custom_commands/recon_suite.py

# Copy PAW Python scripts to installation directory
echo -e "${BLUE}[*] Installing PAW files...${NC}"
sudo cp ./paw.py ${INSTALL_DIR}/bin/
sudo cp ./ascii_art.py ${INSTALL_DIR}/lib/
sudo cp ./tools_registry.py ${INSTALL_DIR}/lib/
sudo cp ./add_custom_tool.py ${INSTALL_DIR}/bin/
sudo cp -r ./custom_commands/* ${INSTALL_DIR}/custom_commands/

# Create symbolic links
echo -e "${BLUE}[*] Creating symbolic links...${NC}"
sudo ln -sf ${INSTALL_DIR}/lib/ascii_art.py ${INSTALL_DIR}/bin/
sudo ln -sf ${INSTALL_DIR}/lib/tools_registry.py ${INSTALL_DIR}/bin/

# Create the paw command executable
echo -e "${BLUE}[*] Creating PAW command...${NC}"
cat > /tmp/paw << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/bin/paw.py "$@"
EOF

sudo mv /tmp/paw /usr/local/bin/
sudo chmod +x /usr/local/bin/paw

# Create the add-paw-tool command
echo -e "${BLUE}[*] Creating add-paw-tool command...${NC}"
cat > /tmp/add-paw-tool << 'EOF'
#!/bin/bash
python3 /usr/local/share/paw/bin/add_custom_tool.py "$@"
EOF

sudo mv /tmp/add-paw-tool /usr/local/bin/
sudo chmod +x /usr/local/bin/add-paw-tool

# Update the Python files to use the new paths
echo -e "${BLUE}[*] Updating file paths in scripts...${NC}"
sudo sed -i "s|from ascii_art import display_ascii_art|from /usr/local/share/paw/lib/ascii_art import display_ascii_art|g" ${INSTALL_DIR}/bin/paw.py
sudo sed -i "s|from tools_registry import get_tools_registry|from /usr/local/share/paw/lib/tools_registry import get_tools_registry|g" ${INSTALL_DIR}/bin/paw.py
sudo sed -i "s|CONFIG_PATH = os.path.expanduser(\"~/.paw/config.ini\")|CONFIG_PATH = \"/etc/paw/config.ini\"|g" ${INSTALL_DIR}/bin/paw.py
sudo sed -i "s|LOG_DIRECTORY = os.path.expanduser(config\['DEFAULT'\].get('log_directory', '~/.paw/logs'))|LOG_DIRECTORY = config\['DEFAULT'\].get('log_directory', '/var/log/paw')|g" ${INSTALL_DIR}/bin/paw.py

# Register custom commands
echo -e "${BLUE}[*] Registering custom commands...${NC}"
sudo add-paw-tool add --name "recon-suite" --category "reconnaissance" \
    --description "Advanced reconnaissance suite for target domains" \
    --usage "recon-suite [options] {target}" \
    --examples "recon-suite -f domains.txt" "recon-suite -d example.com -o report.txt"

# Create default config file
echo -e "${BLUE}[*] Creating configuration file...${NC}"
cat > /tmp/config.ini << EOF
[DEFAULT]
model=MartinRizzo/Ayla-Light-v2:12b-q4_K_M
ollama_host=http://localhost:11434
explain_commands=true
log_commands=true
log_directory=/var/log/paw

[TOOLS]
tools_registry=/usr/local/share/paw/lib/tools_registry.py
EOF

sudo mv /tmp/config.ini ${CONFIG_DIR}/

# Set appropriate permissions
echo -e "${BLUE}[*] Setting file permissions...${NC}"
sudo chown -R root:root ${INSTALL_DIR}
sudo chown -R root:root ${CONFIG_DIR}
sudo chmod -R 755 ${INSTALL_DIR}
sudo chmod -R 644 ${CONFIG_DIR}/config.ini
sudo chmod -R 766 ${LOG_DIR}

# Create user documentation
echo -e "${BLUE}[*] Installing documentation...${NC}"
sudo mkdir -p /usr/local/share/doc/paw
sudo cp README.md /usr/local/share/doc/paw/
sudo cp examples.md /usr/local/share/doc/paw/
sudo cp -r custom_commands/README.md /usr/local/share/doc/paw/custom_commands_guide.md

echo -e "${GREEN}[+] Installation complete!${NC}"
echo -e "${YELLOW}[*] PAW is now installed system-wide. You can run it from anywhere by typing 'paw' in your terminal.${NC}"
echo -e "${YELLOW}[*] To add custom tools, use the 'add-paw-tool' command.${NC}"
echo -e "${YELLOW}[*] Documentation is available in /usr/local/share/doc/paw/${NC}" 