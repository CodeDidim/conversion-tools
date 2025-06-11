# Detailed Setup Guide

## Prerequisites

### All Platforms
- Python 3.7+ 
- Git
- GitHub account with personal access token
- Text editor (VS Code, Notepad++, etc.)

### Platform-Specific
- **Windows**: PowerShell or Command Prompt
- **Linux/macOS**: Terminal with bash/zsh
- **Optional**: Git Bash on Windows for Unix-like commands

## Home Environment Setup

### Step 1: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "Home Workflow Manager"
4. Select scopes: `repo` (all)
5. Generate and save token securely
6. **NEVER share or commit this token**

### Step 2: Run the Generator Script

Save the `generate_workflow_system.py` script and run:

```bash
python generate_workflow_system.py
This creates all necessary files and directories.
Step 3: Run Setup Script
Windows (PowerShell)
powershell# Allow script execution (one-time, as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
cd setup
.\setup-home.ps1
Linux/macOS
bashcd setup
chmod +x setup-home.sh
./setup-home.sh
Step 4: Set Environment Variables
Windows (PowerShell)
powershell# Temporary (current session)
$env:GITHUB_TOKEN = "ghp_your_token_here"

# Permanent (user level)
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_your_token_here", "User")
Windows (Command Prompt)
cmd# Permanent
setx GITHUB_TOKEN "ghp_your_token_here"
Linux/macOS
bash# Add to ~/.bashrc or ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
Step 5: Configure Workflow
Edit .workflow-config.yaml:
yamlgithub:
  owner: "your-github-username"
  repo: "your-repository-name"
  token_env: "GITHUB_TOKEN"
  public_url: "https://github.com/your-username/your-repo.git"

company_git:
  url: "ssh://git@company-server:2222/private-repo.git"

visibility_server:
  port: 8888
  webhook_secret: "generate-strong-secret-here"
  auto_hide_minutes: 15
  allowed_ips: []
Step 6: Create Company Profile
Copy examples/company_profile.yaml.example to conversion-tools/scripts/config_profiles/company_profile.yaml and edit with real values.
Step 7: Setup Network Access
Option A: Port Forwarding

Access router admin panel
Forward external port 8888 to your machine
Note your public IP

Option B: Cloudflare Tunnel
bash# Install cloudflared
# Windows: winget install Cloudflare.cloudflared
# macOS: brew install cloudflare/cloudflare/cloudflared
# Linux: Download from GitHub

# Run tunnel
cloudflared tunnel --url http://localhost:8888
Step 8: Start Visibility Server
bash# Windows
start-server.bat

# Linux/macOS
./start-server
Step 9: Test Setup
bash# Check status
workflow status

# Test visibility control
workflow unhide
workflow hide
Company Environment Setup
Step 1: Run Generator Script
bashpython generate_workflow_system.py
Step 2: Run Company Setup Script
Windows (PowerShell)
powershellcd setup
.\setup-company.ps1
Linux/macOS
bashcd setup
chmod +x setup-company.sh
./setup-company.sh
Step 3: Configure Server Connection
Edit .workflow-config-company.yaml:
yamlvisibility_server:
  url: "http://your-home-public-ip:8888"
  webhook_secret: "same-secret-as-home"

public_remote: "https://github.com/username/repo.git"
private_remote: "ssh://git@company-git:2222/repo.git"

emergency:
  company_backup_remote: "ssh://git@internal:2222/backup.git"
  contact_methods:
    - "Slack: @colleague"
    - "Email: colleague@company.com"
Step 4: Get Company Profile
Copy the same company_profile.yaml from your team to conversion-tools/scripts/config_profiles/
Step 5: Test Setup
bash# Check server connection
workflow check-server

# Test emergency procedures
workflow emergency

# Test visibility request
workflow request-public
Daily Usage
At Home
bash# Start visibility server (keep running)
./start-server

# Work normally
git pullp
git pushp
workflow status
At Company
bash# Request visibility
workflow request-public

# Work with git
git pull public main
git push public main

# Check status
workflow check-server
Troubleshooting
Common Issues

"GitHub token not found"

Ensure GITHUB_TOKEN is set
Restart terminal after setting
Check with: echo $GITHUB_TOKEN (Unix) or echo %GITHUB_TOKEN% (Windows)


"Visibility server offline"

Check home server is running
Verify port forwarding
Test network connectivity
Use workflow emergency for alternatives


"Permission denied"

Windows: Run PowerShell as Administrator
Unix: Use chmod +x on scripts


"Module not found"

Install dependencies: pip install requests pyyaml flask



Security Checklist
Home Setup

 GitHub PAT is in environment variable only
 workflow.py has appropriate permissions
 Visibility server uses strong webhook secret
 Port forwarding is limited to port 8888

Company Setup

 workflow.py is NOT present
 Only workflow-company.py exists
 No GitHub credentials anywhere
 Emergency procedures tested