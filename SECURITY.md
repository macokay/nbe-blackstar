# Security

## Reporting a vulnerability

Please report privately: [open a private advisory](https://github.com/macokay/nbe-blackstar/security/advisories/new). Do not open a public issue. Expect a first answer within a few days.

## Supported versions

Only the latest release receives fixes. The project is under development.

## Security model

- The bridge only reads from the controller (discovery and `get()`). Writes are disabled unless `NBE_ALLOW_WRITE=true` is set, and no writable entities are published.
- The controller protocol is unauthenticated UDP apart from the pincode sent in each frame. Keep the controller on a segment that only the bridge can reach.
- Run the container as the non-root user it ships with. Do not publish the MQTT broker to the internet.

## Secrets

- `NBE_PASS` (controller pincode, shown on the burner display) and `MQTT_PASS` come from the environment only. Use an env file with mode 600, a secret manager or your keychain. Never put them in a config file or in git.
- Do not share photos of the controller's system settings screen. It shows the pincode.
- If a secret leaks: rotate it on the controller (menu 18) and on the MQTT broker first, then clean up history.

## Supply chain

- Actions are pinned to commit SHAs and updated by Dependabot.
- Release images are multi-arch, carry an SBOM and build provenance, and are scanned with Trivy in CI.
