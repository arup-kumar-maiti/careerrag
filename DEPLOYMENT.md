# Deployment Guide

Deploy to a VPS with a custom domain. Set up the server with [launchpad](https://github.com/arup-kumar-maiti/launchpad).

## Configure and Upload

```bash
careerrag init
```

```bash
sed \
  -e 's/model: llama3.2/model: claude-sonnet-4-20250514/' \
  -e 's/provider: ollama/provider: claude/' \
  -e 's/username: John Doe/username: Your Name/' \
  .careerrag/config.yml > .careerrag/tmp.yml && mv .careerrag/tmp.yml .careerrag/config.yml
```

```bash
careerrag index --docs ~/documents
```

```bash
scp -r .careerrag/* ssh.example.com:/root/careerrag-data/
```

## Create the Application

1. Open `https://dokploy.example.com`, complete onboarding
2. Add Docker Registry — URL: `ghcr.io`, Username: `<github-username>`, Password: GitHub PAT (classic) with `read:packages`
3. Create a project and application with image `ghcr.io/arup-kumar-maiti/careerrag:latest`
4. Run command: `careerrag serve`
5. Volume Bind Mount: `/root/careerrag-data` → `/app/.careerrag`
6. Environment: `ANTHROPIC_API_KEY=sk-ant-...`
7. Domain: `example.com`, Port: `8000`
8. Domain for Phoenix tracing UI: `phoenix.example.com`, Port: `3300`
9. Deploy and open `https://example.com`
