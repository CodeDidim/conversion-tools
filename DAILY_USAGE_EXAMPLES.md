# At Home (with GitHub token):
## Morning - start work
cd ~/embedded-test

## Pull latest (auto-handles visibility)
git pullp  # Or: python conversion-tools/workflow.py pull

## Work on features...
vim src/sensor_simulator.py

## Commit and push (auto-handles visibility)
git add .
git commit -m "Add sensor calibration"
git pushp  # Or: python conversion-tools/workflow.py push

## The repo is automatically made public during push, then hidden again

# At Company (no GitHub token, only public repo access):
## Option 1: Using remote desktop make it public
# (They run: python conversion-tools/workflow.py unhide)

## Option 2: Auto-visibility during operations
cd ~/embedded-test

## Pull latest
git pull public main  # Works if repo is public

## Convert to private mode
python conversion-tools/workflow.py private

## Work with real values
cat config/hardware_config.yaml  # Has real IPs, passwords

## Push to company's internal git
git push private private/main

## Convert back to public before pushing
python conversion-tools/workflow.py public

## Push to GitHub (someone needs to unhide it first)
git push public main

## Or using remote desktop pull your changes 


# Collaborative Workflow (remote desktop):

## When we are in the company and we need to push, using remote desktop
python conversion-tools/workflow.py unhide

## "It's public now, you can push"

## After confirming push is done
python conversion-tools/workflow.py hide

# Key Features of This Solution

## Automatic Visibility Management: When pushing/pulling from home, the repo is made public for just the duration of the operation, then immediately hidden again.

## Company-Friendly: At the company, you can work with public repos without authentication. Someone at home can temporarily unhide it when needed.

## Smart Location Detection: The script detects whether you're at home (has GITHUB_TOKEN) or at company (no token).

## Safety First: Multiple validation steps ensure no private data leaks to public repo.

## Git Aliases: Simple commands like git pushp handle all the complexity.