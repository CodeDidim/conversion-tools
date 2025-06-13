# Manual Workflow Test Scenarios

## Scenario 1: New Developer Onboarding
1. Developer clones public repo at company
2. Attempts to run without setup
3. Runs init command
4. Attempts to pull without repo being public
5. Gets clear instructions
6. Successfully completes first workflow

## Scenario 2: Emergency Push from Company
1. Critical bug found at company
2. Need to push fix immediately
3. Repo is currently private
4. Test emergency procedures
5. Verify fix can be deployed

## Scenario 3: Accidental Secret Exposure
1. Developer forgets to convert to public
2. Attempts to push private version
3. Validation catches secrets
4. Developer corrects mistake
5. Successful push of clean version
