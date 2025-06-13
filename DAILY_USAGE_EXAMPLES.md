# At Home (with GitHub token)
## Morning - start work
cd ~/embedded-test

## Pull latest
python conversion-tools/scripts/github_visibility.py unhide
git pull origin main
python conversion-tools/scripts/github_visibility.py hide

## Work on features...
vim src/sensor_simulator.py

## Commit and push
git add .
git commit -m "Add sensor calibration"
python conversion-tools/scripts/github_visibility.py unhide
git push origin main
python conversion-tools/scripts/github_visibility.py hide

# At Company (no GitHub token, only public repo access)
python conversion-tools/workflow.py private
# Work with real values...

# Push to company's internal git
git push private private/main

# Convert back to public before pushing to GitHub
python conversion-tools/workflow.py public
# Someone at home must unhide first

