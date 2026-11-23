# Home Assistant App: ControllerX

[![ControllerX total downloads](https://img.shields.io/github/downloads/xaviml/controllerx/controllerx.zip?style=for-the-badge&label=total%20downloads&logo=github&color=18BCF2&displayAssetName=false)](https://github.com/xaviml/controllerx/releases)

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
├── secrets.yaml        Optional secrets for your apps (yours)
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

AppDaemon picks up changes to these files on its own, no restart is needed,
unless [`production_mode`](#option-production_mode) is on.

### AppDaemon configuration

There's no `appdaemon.yaml` to edit: the app generates the AppDaemon
configuration on every start, from the app options below and the location and
time zone of your Home Assistant, and keeps it in its private storage.

It only has what ControllerX needs, so AppDaemon uses as few resources as
possible: no web interface, no worker threads (ControllerX runs everything
in AppDaemon's event loop) and, with MQTT, only the topics of your
controllers. To see it, set `log_level` to `debug` and restart the app: it's
printed at the beginning of the log.

If you had an `appdaemon.yaml` from an earlier version of the app, the app
moves its MQTT plugin settings to the app options and keeps the file as
`appdaemon.yaml.bak`, which you can delete.

### `apps/controllerx/`

This folder holds the ControllerX code that ships with the app. It's replaced
on every start, so any change made in it is lost. To update ControllerX,
update the app.

## Options

```yaml
log_level: info
python_packages: []
production_mode: false
mqtt_enabled: false
mqtt_host: 192.168.1.10
mqtt_port: 1883
mqtt_username: my_user
mqtt_password: my_password
mqtt_client_id: controllerx_living_room
```

### Option: `log_level`

How verbose the AppDaemon logs are: `trace`, `debug`, `info`, `notice`,
`warning`, `error` or `fatal`. Defaults to `info`.

### Option: `python_packages`

Extra Python packages to install into AppDaemon on every start. ControllerX
itself doesn't need any.

### Option: `production_mode`

By default, AppDaemon checks the `apps` folder every second, so changes to
`apps.yaml` are applied right away. Once your configuration is stable, turn
this on to stop those checks and save some resources. Changes to `apps.yaml`
then need an app restart to apply. Defaults to `false`.

### Option: `mqtt_enabled`

Connects AppDaemon to an MQTT broker. It's needed by the `mqtt` and `tasmota`
integrations, the `z2m` integration with `listen_to: mqtt` and
`Z2MLightController` with `mode: mqtt`. See
[Enable MQTT plugin](https://xaviml.github.io/controllerx/others/enable-mqtt-plugin).

If you use the Mosquitto broker app, turning this on is enough: the app gets
the broker address and credentials from Home Assistant.

### Options: `mqtt_host`, `mqtt_port`, `mqtt_username` and `mqtt_password`

The MQTT broker to connect to, for brokers other than the Mosquitto broker
app. `mqtt_host` goes without the port, which defaults to 1883.

### Option: `mqtt_client_id`

The client ID the app connects to the MQTT broker with. The broker disconnects
a client when another one connects with the same ID, so it must be unique on
the broker.

Leave it empty and the app generates one on its first start, such as
`controllerx_1a2b3c4d`, and keeps it. Each install gets a different one, so
several installs of this app (for example, in two Home Assistant instances)
and the AppDaemon app can use the same broker. Set it only if your broker
needs a known client ID, for example for its access rules.

## Using it together with the AppDaemon app

This app runs its own AppDaemon instance with its own files, so it can run
next to the community AppDaemon app. Each controller must be configured in
only one of them: if it's in both, every button press runs twice (for
example, a toggle that turns the light on and off again).

To move ControllerX from the AppDaemon app to this app:

1. Copy your ControllerX apps from the AppDaemon app's `apps.yaml` into this
   app's `apps/apps.yaml`. If you use the MQTT plugin, turn on
   `mqtt_enabled` in this app's options.
2. Remove those apps and the `apps/controllerx/` folder from the AppDaemon
   app, and restart it.
3. Start (or restart) this app.

Your other AppDaemon apps can stay in the AppDaemon app.

## Support

- [ControllerX documentation](https://xaviml.github.io/controllerx/)
- [Report an issue](https://github.com/xaviml/controllerx/issues)
