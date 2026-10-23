# Runbook

## Deploy (Docker)

```
cp .env.local.example .env.local   # fill in the values
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f nbe
```

From a release image instead of building: `docker run -d --name nbe --restart unless-stopped -v nbe-data:/var/lib/nbe --env-file .env.local ghcr.io/macokay/nbe-blackstar:<version>`.

Health: `docker inspect -f '{{.State.Health.Status}}' nbe`. The container is unhealthy when the controller has not answered for 5 minutes.

## Deploy (systemd)

See the README. Logs: `journalctl -u nbe -f`.

## Verify after a change

1. `docker logs nbe` shows `Connected to MQTT broker` and no warnings.
2. Entities update in Home Assistant, and no `Value error` appears in its log.
3. The retained `<device-id>/bridge/state` topic is `online`.

## Moving from the bridge to the HACS integration

Only one of them may run against the controller.

1. Stop the bridge: `docker compose -f deploy/docker-compose.yml stop nbe`.
2. In Home Assistant, Settings, Entities, filter on "unavailable" and delete the old `nbe_*` entities from the bridge.
3. Remove the bridge's entries and add the NBE Black Star integration again, so the entities get clean ids without `_2`. The energy file `nbe_blackstar_energy_<serial>.json` is kept.
4. Optional: to carry the old total forward, set `kwh` in the energy file to the old total plus the new one before the next restart.

## Rollback

Run the previous image tag (or check out the previous tag and rebuild), then restart the container. The retained discovery messages are replaced on the next start.

## Stale or wrong entities after changing the device id

Publish an empty retained payload to the old `homeassistant/<type>/<old-id>/<name>/config` topics, then restart Home Assistant.

## Leaked secret

1. Rotate the controller pincode and the MQTT password.
2. Remove the value from logs and issues.
3. Rewrite git history only after the maintainer approves it explicitly.
