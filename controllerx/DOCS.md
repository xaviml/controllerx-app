# Home Assistant App: ControllerX

[ControllerX](https://xaviml.github.io/controllerx/) lets you create
controller-based automations for your lights, media players, covers and
switches with a few lines of YAML.

This app runs its own [AppDaemon](https://appdaemon.readthedocs.io/) instance
with ControllerX preinstalled and kept up to date. It's an alternative to
installing ControllerX manually into the AppDaemon app.

## Installation

1. Add this repository to your Home Assistant app store:
   `https://github.com/xaviml/controllerx-app`
2. Install the **ControllerX** app and start it.
3. Configure your controllers in `apps/apps.yaml` (see below).

## Files

The app keeps its files in its own configuration folder. You can reach it
with the Studio Code Server or Samba apps, under
`/addon_configs/<id>_controllerx/`:

```text
/addon_configs/<id>_controllerx/
├── appdaemon.yaml      AppDaemon configuration (yours)
├── secrets.yaml        Optional secrets for appdaemon.yaml and apps (yours)
└── apps/
    ├── apps.yaml       Your ControllerX apps (yours)
    ├── *.yaml          Optionally, more files with apps (yours)
    └── controllerx/    ControllerX code, replaced on every start
```

### `apps/apps.yaml`

This is where you define your controllers, following the
[ControllerX configuration](https://xaviml.github.io/controllerx/start/configuration).
The app creates it with a commented example on first start and never changes
it afterwards. You can split your apps into several YAML files inside `apps/`.

AppDaemon picks up changes to these files on its own, no restart is needed.

### `appdaemon.yaml`

The app creates it on first start, with the location and time zone of your
Home Assistant and a connection to Home Assistant already set up. After that,
it's yours to change; restart the app to apply changes. On every start, the app
only makes sure the Home Assistant token and the web interface address are set.

To use the z2m integration with `listen_to: mqtt`, enable the MQTT plugin as
explained in [Enable MQTT plugin](https://xaviml.github.io/controllerx/others/enable-mqtt-plugin).
With the Mosquitto broker app, use `core-mosquitto` as `client_host`, and keep
the password in `secrets.yaml`:

```yaml
# appdaemon.yaml
appdaemon:
  plugins:
    MQTT:
      type: mqtt
      namespace: mqtt
      client_host: core-mosquitto
      client_user: my_user
      client_password: !secret mqtt_password
```

```yaml
# secrets.yaml
mqtt_password: my_password
```

### `apps/controllerx/`

This folder holds the ControllerX code that ships with the app. It's replaced
on every start, so any change made in it is lost. To update ControllerX,
update the app.

## Options

```yaml
log_level: info
python_packages: []
```

### Option: `log_level`

How verbose the AppDaemon logs are: `trace`, `debug`, `info`, `notice`,
`warning`, `error` or `fatal`. Defaults to `info`.

### Option: `python_packages`

Extra Python packages to install into AppDaemon on every start, for example
for your own apps. ControllerX itself doesn't need any.

## Web interface

The AppDaemon web interface isn't needed for ControllerX, so its port (5050)
is disabled by default. To use it, set a port in the app's **Network**
settings. If you also run the AppDaemon app, pick a different port than it,
for example 5051.

## Using it together with the AppDaemon app

This app runs its own AppDaemon instance with its own files, so it can run
next to the community AppDaemon app. Each controller must be configured in
only one of them: if it's in both, every button press runs twice (for
example, a toggle that turns the light on and off again).

To move ControllerX from the AppDaemon app to this app:

1. Copy your ControllerX apps from the AppDaemon app's `apps.yaml` into this
   app's `apps/apps.yaml`. If you use the MQTT plugin, copy its configuration
   from `appdaemon.yaml` as well.
2. Remove those apps and the `apps/controllerx/` folder from the AppDaemon
   app, and restart it.
3. Start (or restart) this app.

Your other AppDaemon apps can stay in the AppDaemon app.

## Support

- [ControllerX documentation](https://xaviml.github.io/controllerx/)
- [Report an issue](https://github.com/xaviml/controllerx/issues)
