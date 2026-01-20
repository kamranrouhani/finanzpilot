# Prerequisites - Setup Before Running Ralph

Complete ALL steps before starting any Ralph loop. This ensures the agent can work without interruption.

## 1. System Requirements Check

```bash
# Verify NVIDIA driver
nvidia-smi
# Should show RTX 4070 with ~12GB VRAM

# Verify Docker
docker --version
# Should be 24.x or higher

# Verify Docker Compose
docker compose version
# Should be v2.x

# Verify Git
git --version
# Should be 2.x

# Verify Node.js
node --version
# Should be v20.x LTS

# Verify pnpm
pnpm --version
# Should be 10.x
```

## 2. Install Required Software

### Docker with NVIDIA Support (Pop!_OS 22.04)
```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Node.js 20 LTS
```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

### Python 3.12 (for local testing without Docker)
```bash
# Pop!_OS / Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

### GitHub CLI (for PR operations)
```bash
sudo apt install gh
gh auth login
```

## 3. Create Project Directory

```bash
# Create project root
mkdir -p ~/projects/finanzpilot
cd ~/projects/finanzpilot

# Initialize git
git init
git branch -M main

# Create GitHub repo (or do manually on GitHub)
gh repo create finanzpilot --private --source=. --remote=origin

# Set up git config
git config user.name "Your Name"
git config user.email "your@email.com"
```

## 4. Pre-pull Docker Images

This saves significant time during the first Ralph run:

```bash
# Pull base images (do this the night before)
docker pull postgres:16-alpine
docker pull node:20-alpine
docker pull python:3.12-slim
docker pull ollama/ollama:latest

# Pre-pull Ollama models (this takes 10-20 minutes)
# Start Ollama temporarily
docker run -d --gpus all --name ollama-temp -p 11434:11434 ollama/ollama

# Pull models
docker exec ollama-temp ollama pull qwen2.5-vl:7b
docker exec ollama-temp ollama pull qwen2.5:7b

# Verify models
docker exec ollama-temp ollama list

# Stop and remove temp container (models persist in volume)
docker stop ollama-temp
docker rm ollama-temp
```

## 5. Create Docker Volume for Ollama Models

```bash
# Create named volume to persist models
docker volume create ollama_models

# Copy pre-pulled models to named volume
docker run --rm -v ollama_models:/dest -v ~/.ollama:/src alpine cp -r /src/models /dest/
```

## 6. Prepare Sample Data

### Finanzguru Export
1. Open Finanzguru app
2. Go to Settings → Export
3. Export as XLSX
4. Save to `~/projects/finanzpilot/sample-data/finanzguru_export.xlsx`

### Sample Receipts (optional, for testing)
```bash
mkdir -p ~/projects/finanzpilot/sample-data/receipts
# Add 2-3 sample receipt images (jpg/png) to this folder
```

## 7. Create Environment Files

```bash
cd ~/projects/finanzpilot

# Create .env file (will be gitignored)
cat > .env << 'EOF'
# Database
POSTGRES_USER=finanzpilot
POSTGRES_PASSWORD=localdevpassword123
POSTGRES_DB=finanzpilot
DATABASE_URL=postgresql://finanzpilot:localdevpassword123@postgres:5432/finanzpilot

# Backend
JWT_SECRET=dev-secret-change-in-production-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
OLLAMA_HOST=http://ollama:11434

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Create .env.example (committed to git)
cat > .env.example << 'EOF'
POSTGRES_USER=finanzpilot
POSTGRES_PASSWORD=<your-secure-password>
POSTGRES_DB=finanzpilot
DATABASE_URL=postgresql://finanzpilot:<password>@postgres:5432/finanzpilot
JWT_SECRET=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
OLLAMA_HOST=http://ollama:11434
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

## 8. Install Claude Code & Ralph Plugin

```bash
# Install Claude Code (if not already)
pnpm install -g @anthropic-ai/claude-code

# Start Claude Code and install Ralph
claude

# Inside Claude Code:
/plugin install ralph-wiggum@claude-plugins-official
```

## 9. Configure GitHub Actions Secrets

Go to your repo → Settings → Secrets and variables → Actions

Add these secrets:
- None required for local-only CI (tests run in containers)

## 10. Verify Everything Works

```bash
# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Test Ollama responds
docker run -d --gpus all --name ollama-test -p 11434:11434 -v ollama_models:/root/.ollama ollama/ollama
sleep 5
curl http://localhost:11434/api/tags
docker stop ollama-test && docker rm ollama-test

# Test Node
node -e "console.log('Node OK:', process.version)"

# Test Python
python3.12 -c "print('Python OK')"

# Test GitHub CLI
gh auth status
```

## 11. Free Up Resources

Before starting Ralph:

```bash
# Stop any running Docker containers
docker stop $(docker ps -q) 2>/dev/null

# Clear Docker cache if low on disk
docker system prune -f

# Check available disk space (need at least 20GB free)
df -h ~

# Check memory
free -h
```

## 12. Checklist Before Running Ralph

- [ ] NVIDIA driver working (`nvidia-smi` shows GPU)
- [ ] Docker with GPU support working
- [ ] Ollama models pre-pulled (qwen2.5-vl:7b, qwen2.5:7b)
- [ ] Node.js 20 installed
- [ ] Git repo initialized and connected to GitHub
- [ ] `.env` file created with all variables
- [ ] Sample Finanzguru export available
- [ ] At least 20GB free disk space
- [ ] At least 16GB free RAM
- [ ] Claude Code installed with Ralph plugin
- [ ] No other GPU-intensive processes running

## Troubleshooting

### "CUDA out of memory"
- Close any browser tabs with GPU acceleration
- Stop other Docker containers
- Reduce model to `qwen2.5-vl:2b` temporarily

### "Permission denied" on Docker
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Ollama model not found
```bash
# Re-pull models
docker exec -it <ollama-container> ollama pull qwen2.5-vl:7b
```

### Database connection refused
```bash
# Check PostgreSQL is running
docker logs <postgres-container>
# Wait for "database system is ready to accept connections"
```

## Time Estimates

| Task | Time |
|------|------|
| Install NVIDIA Container Toolkit | 5 min |
| Pull Docker images | 10 min |
| Pull Ollama models | 15-20 min |
| Create env files | 5 min |
| Verify setup | 5 min |
| **Total** | **~45 min** |

---

Once all prerequisites are complete, proceed to `docs/PHASE_1.md` for the first Ralph loop.
