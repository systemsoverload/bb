# bb - Bitbucket Cloud CLI

A modern command-line interface for interacting with Bitbucket Cloud.

## Features

- **Pull Request Management**
  - List, create, and review pull requests
  - Smart reviewer selection with CODEOWNERS and default reviewers integration
- Rich terminal UI for PR reviews

- **Configuration**
  - User-defined command aliases
  - TOML-based configuration

## Installation

```bash
pipx install bitbucket-cloud-cli
```

## Quick Start

1. Login to Bitbucket:
```bash
bb auth login
```

2. List your pull requests:
```bash
bb pr list --mine
```

3. Create a new pull request:
```bash
bb pr create
```

4. Review pull requests interactively:
```bash
bb pr review
```

Configuration is stored in `~/.config/bb/config.toml`:

```toml
[auth]
username = "your-username"
app_password = "your-app-password"

# Optional aliases added through `bb alias`
[alias]
prm = "pr list --mine"
prr = "pr list --reviewing"
```

## Dev

```bash
git clone git@github.com/systemsoverload/bb
cd bb
rye sync
rye test
pipx install -e ./ --force
```
