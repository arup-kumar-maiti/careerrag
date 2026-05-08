# Deployment Guide

Set up the server with [launchpad](https://github.com/arup-kumar-maiti/launchpad).

## Local

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
ssh ssh.example.com 'sudo mkdir -p /opt/careerrag/.careerrag'
scp -r .careerrag/* ssh.example.com:/opt/careerrag/.careerrag/
```

## Server

```bash
sudo python3 -m venv /opt/careerrag/venv
sudo /opt/careerrag/venv/bin/pip install careerrag
```

```bash
cd /opt/careerrag
export ANTHROPIC_API_KEY=sk-ant-...
sudo -E /opt/careerrag/venv/bin/careerrag deploy
```

Verify:

```bash
curl http://localhost:8000
curl http://localhost:3300
```

## Useful Commands

```bash
sudo systemctl status careerrag
sudo systemctl restart careerrag
sudo systemctl stop careerrag
sudo journalctl -u careerrag -f
```
