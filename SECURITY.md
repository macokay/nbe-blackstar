# Security

This is a fork for one NBE Black Star controller.

## Model
- The bridge only reads from the controller (discovery and `get()`). Writes are disabled unless `NBE_ALLOW_WRITE=true` is set, and no writable entities are published.
- The controller's protocol is unauthenticated UDP apart from the pincode in each frame. Keep it on a segment that only the bridge can reach.

## Secrets
- `NBE_PASS` (controller pincode from the burner's display) and `MQTT_PASS` come from the environment only. Use `.env.local` (gitignored) or the macOS keychain, never `config.json`.
- Do not share photos of the controller's System settings screen (menu 18). It shows the pincode.
- If a secret is committed or shared: rotate it on the controller (menu 18) and on the MQTT broker.

## Reporting
Open a private issue or contact the repo owner directly.
