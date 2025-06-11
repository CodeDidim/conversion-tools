#!/usr/bin/env python3
"""
Cross-platform setup script for workflow system
Works on Windows, Linux, and macOS
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

class WorkflowSetup:
    def __init__(self, environment='home'):
        self.environment = environment
        self.is_windows = platform.system() == 'Windows'
        self.is_home = environment == 'home'
        
    def check_python(self):
        """Check Python installation"""
        print("Checking Python installation...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 6):
            print("❌ Python 3.6+ required!")
            sys.exit(1)
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} found")
        
    def install_dependencies(self):
        """Install required packages"""
        print("\nInstalling dependencies...")
        
        packages = ['requests', 'pyyaml']
        if self.is_home:
            packages.append('flask')
            
        for package in packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package])
            
    def check_environment(self):
        """Check environment variables"""
        if self.is_home:
            token = os.environ.get('GITHUB_TOKEN')
            if not token:
                print("\n⚠️  GITHUB_TOKEN not set!")
                print("\nTo set on Windows:")
                print('  PowerShell: [Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_token", "User")')
                print('  CMD: setx GITHUB_TOKEN "ghp_token"')
                print("\nTo set on Linux/Mac:")
                print('  export GITHUB_TOKEN="ghp_token"')
                print('  echo \'export GITHUB_TOKEN="ghp_token"\' >> ~/.bashrc')
                
    def create_directories(self):
        """Create directory structure"""
        print("\nCreating directories...")
        
        dirs = [
            'conversion-tools',
            'conversion-tools/scripts',
            'conversion-tools/scripts/config_profiles',
            'conversion-tools/private-overlay',
            'logs'
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
    def check_scripts(self):
        """Check for required scripts"""
        print("\nChecking scripts...")
        
        if self.is_home:
            required = ['workflow.py', 'visibility-server.py']
        else:
            required = ['workflow-company.py']
            
        missing = []
        for script in required:
            path = Path('conversion-tools') / script
            if not path.exists():
                missing.append(script)
                
        if missing:
            print(f"\n⚠️  Missing scripts: {', '.join(missing)}")
            print("Please copy these to the conversion-tools directory")
            
        # Security check for company
        if not self.is_home:
            home_script = Path('conversion-tools/workflow.py')
            if home_script.exists():
                print("\n❌ SECURITY WARNING: workflow.py found at company!")
                response = input("Delete it? (y/n): ")
                if response.lower() == 'y':
                    home_script.unlink()
                    print("✓ Removed workflow.py")
                    
    def create_shortcuts(self):
        """Create convenient shortcuts"""
        print("\nCreating shortcuts...")
        
        if self.is_windows:
            # Windows batch files
            if self.is_home:
                with open('workflow.bat', 'w') as f:
                    f.write('@echo off\n')
                    f.write('python conversion-tools\\workflow.py %*\n')
                    
                with open('start-server.bat', 'w') as f:
                    f.write('@echo off\n')
                    f.write('title Visibility Server\n')
                    f.write('echo Starting visibility server...\n')
                    f.write('python conversion-tools\\visibility-server.py\n')
                    f.write('pause\n')
            else:
                with open('workflow.bat', 'w') as f:
                    f.write('@echo off\n')
                    f.write('python conversion-tools\\workflow-company.py %*\n')
        else:
            # Unix shell scripts
            if self.is_home:
                with open('workflow', 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write('python3 conversion-tools/workflow.py "$@"\n')
                os.chmod('workflow', 0o755)
                
                with open('start-server', 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write('echo "Starting visibility server..."\n')
                    f.write('python3 conversion-tools/visibility-server.py\n')
                os.chmod('start-server', 0o755)
            else:
                with open('workflow', 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write('python3 conversion-tools/workflow-company.py "$@"\n')
                os.chmod('workflow', 0o755)
                
    def initialize_workflow(self):
        """Initialize the workflow system"""
        print("\nInitializing workflow...")
        
        script = 'workflow.py' if self.is_home else 'workflow-company.py'
        script_path = Path('conversion-tools') / script
        
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path), 'init'])
        else:
            print(f"⚠️  Cannot initialize - {script} not found")
            
    def show_next_steps(self):
        """Show next steps"""
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        
        if self.is_home:
            print("1. Set GITHUB_TOKEN environment variable")
            print("2. Update .workflow-config.yaml with your GitHub details")
            print("3. Start visibility server:")
            if self.is_windows:
                print("   start-server.bat")
            else:
                print("   ./start-server")
            print("4. Configure port forwarding for port 8888")
        else:
            print("1. Update .workflow-config-company.yaml with server details")
            print("2. Get company_profile.yaml from your team")
            print("3. Test server connection:")
            if self.is_windows:
                print("   workflow check-server")
            else:
                print("   ./workflow check-server")
            print("\n⚠️  REMEMBER: Never copy workflow.py to company!")
            
    def run(self):
        """Run the setup process"""
        print(f"{'🏠 HOME' if self.is_home else '🏢 COMPANY'} Workflow Setup")
        print("=" * 40)
        
        self.check_python()
        self.install_dependencies()
        self.check_environment()
        self.create_directories()
        self.check_scripts()
        self.create_shortcuts()
        self.initialize_workflow()
        self.show_next_steps()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup workflow environment')
    parser.add_argument('environment', choices=['home', 'company'],
                       help='Environment to setup')
    
    args = parser.parse_args()
    
    setup = WorkflowSetup(args.environment)
    setup.run()

if __name__ == '__main__':
    # If no arguments, ask interactively
    if len(sys.argv) == 1:
        print("Workflow Setup")
        print("=" * 40)
        print("1. Home environment (with GitHub PAT)")
        print("2. Company environment (no PAT)")
        
        choice = input("\nSelect environment (1/2): ")
        
        if choice == '1':
            setup = WorkflowSetup('home')
        elif choice == '2':
            setup = WorkflowSetup('company')
        else:
            print("Invalid choice!")
            sys.exit(1)
            
        setup.run()
    else:
        main()