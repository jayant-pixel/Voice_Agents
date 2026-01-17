# Documentation

Detailed documentation for the Voice AI Agent system.

## Contents

- [KB_MANAGER_MANUAL.md](./KB_MANAGER_MANUAL.md) - Complete guide to the Knowledge Base system

## Quick Reference

### Knowledge Base Commands

```bash
python tools/ingest.py              # Ingest documents
python tools/ingest.py --stats      # View stats
python tools/test_kb.py             # Test queries
```

### Run Agent

```bash
python agent.py dev                 # Development mode
```

### Configuration

- Edit `persona.yaml` for agent personality
- Edit `.env` for API keys
