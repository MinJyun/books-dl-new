
#!/bin/bash
# Description: Initialize Git repository and prepare for GitHub push

# 1. Initialize Git
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
else
    echo "Git repository already initialized."
fi

# 2. Create .gitignore
echo "Creating .gitignore..."
cat > .gitignore <<EOF
__pycache__/
*.pyc
.DS_Store
cookie.txt
cookie.json
*.epub
*.pdf
.venv/
venv/
EOF

# 3. Add files
echo "Adding files to staging..."
git add .
git add -f README.md  # Force add README if ignored by mistake
git add -f main.py

# 4. Commit
echo "Committing initial version..."
git commit -m "Initial commit: Books Downloader (Python)"

# 5. Instructions for pushing
echo ""
echo "=========================================="
echo "✅ Repository initialized and committed!"
echo "=========================================="
echo "To push to GitHub, run the following commands:"
echo ""
echo "  1. Create a new repository on GitHub (https://github.com/new)"
echo "  2. Run:"
echo "     git remote add origin <YOUR_GITHUB_REPO_URL>"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
