# Credits

## Protocol
- **Anders Nylund** (2013): reverse engineering of the NBE controller UDP protocol and the original Python implementation (`src/protocol.py`, `src/frames.py`). Licensed GPL-2.0-or-later.

## Original integration
- **e1z0** (https://github.com/e1z0): the Home Assistant / MQTT bridge this project grew from (`src/nbe.py`, `src/ha_classes.py`, `src/settings.py`, schema and Docker setup). Licensed BSD-3-Clause.

## Contributors (upstream history)
- **Jonas Overgaard**: upstream contribution.
- Upstream Docker image maintainer (`nulldevil/nbe`): packaging of the original image.

## Fork and modernization
- **Mac O Kay** (@macokay): fork, read-only hardening, Docker deployment, Home Assistant entity overhaul, tests.

Upstream sources: https://github.com/e1z0/nbe-blackstar-homeassistant
