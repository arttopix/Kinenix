# Make Greeting
> Description: Builds the greeting row for one name. flow.md calls it once per name with inputs {"name": ...}. As a subflow of this bundle, it reads ${config.greeting} from the bundle's config/config.json, and relative paths would resolve against the bundle folder.
> Version: 1.0.0

## Variables
- `name`: ""

## Steps

### 1. Stop Without A Name (`flow.fail`)
- **condition:** `${name} is empty`
- **message:** make_greeting needs a name in its inputs

### 2. Return The Greeting Row (`flow.return`)
- **value:** {"Name": "${name}", "Greeting": "${config.greeting}, ${name}!"}
