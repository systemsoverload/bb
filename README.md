# bb

Bitbucket CLI tools

## Installation

### From source
`git clone git@github.com:systemsoverload/bb.git`
`cd bb && pipx install .`

### From pypi
`pipx install bitbucket-cloud-cli`

### Enabling auto-completion

#### Bash

Add this to `~/bashrc`
```eval "$(_FOO_BAR_COMPLETE=bash_source foo-bar)"```

#### Zsh

Add this to `~/zshrc`
```eval "$(_FOO_BAR_COMPLETE=bash_source foo-bar)"```

#### Fish

Add this to `~/.config/fish/completions/foo-bar.fish`:
```eval "$(_FOO_BAR_COMPLETE=bash_source foo-bar)"```

## Usage

`bb auth login`


## Dev

`rye sync`
`rye test`
`pipx install -e ./ --force`
