# Git Manager for SysCan project
# Usage: .\git_manager.ps1 {pull|push|commit|status|branch}

$REPO_PATH = "C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository"
$REMOTE = "https://github.com/gyan4it/syscan.git"

cd $REPO_PATH -ErrorAction Stop

switch ($args[0]) {
    "pull" {
        Write-Host "Pulling latest changes..."
        git pull $REMOTE master
        break
    }
    "push" {
        Write-Host "Pushing to GitHub..."
        git push $REMOTE master
        break
    }
    "commit" {
        if (-not $args[1]) {
            Write-Host "Usage: .\git_manager.ps1 commit 'message'" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Committing: $($args[1])"
        git add .
        git commit -m $args[1]
        break
    }
    "status" {
        Write-Host "=== Git Status ==="
        git status
        Write-Host "`n=== Recent Commits ==="
        git log --oneline -5
        break
    }
    "branch" {
        if (-not $args[1]) {
            Write-Host "Usage: .\git_manager.ps1 branch <name>" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Creating branch: $($args[1])"
        git checkout -b $args[1]
        break
    }
    default {
        Write-Host "Usage: .\git_manager.ps1 {pull|push|commit|status|branch}" -ForegroundColor Yellow
        Write-Host "  pull              - Pull from master"
        Write-Host "  push              - Push to master"
        Write-Host "  commit 'msg'    - Commit with message"
        Write-Host "  status            - Show git status"
        Write-Host "  branch <name>    - Create new branch"
    }
}
