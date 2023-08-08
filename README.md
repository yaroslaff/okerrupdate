# okerrupdate - client-side okerr module and utilities

## Installation 

```shell
# newer method with pipx
sudo pipx install okerrupdate

# old method with pip3, if you cannot install pipx
sudo pip3 install okerrupdate


sudo okerrmod --init # enable few basic modules, create /etc/cron.d/ job, create okerrupdate config template
sudo vim /etc/okerr/okerrupdate
```

and modify okerrupdate file:
~~~
# Stub for okerrmod            
PREFIX=braconnier:
OKERR_TEXTID=
OKERR_SECRET=
OKERR_URL=
OKERR_DIRECT=0

OKERR_MOD_AVAIL=
~~~
or provide values to `okerrmod --init` as option values (e.g. `okerrmod --init --textid MyTextid`).


## Basic usage

### okerrupdate utility

okerrupdate is small script which updates/creates indicators in okerr project. 

This will create simplest indicator 'myindicator' with all default settings (type 'heartbeat', policy 'Default').
Indicator will send alert if it will be updated to 'ERR' or if will not be updated for some time 
(Default policy period+patience).
```shell
$ okerrupdate myindicator OK
okerr updated (200 OK) myindicator@okerr = OK
```

This will create numerical indicator 'temp' with current value 36.6, and policy 'Daily'. Will send alert if not updated 
for a day or if value will be over maxlim (37).
```shell
$ okerrupdate -p Daily -m 'numerical|maxlim=37' temp 36.6
okerr updated (200 OK) temp@okerr = 36.6
```

Project TextID and secret is read from `/etc/okerr/okerrupdate` file or `OKERR_TEXTID` and `OKERR_SECRET` environment 
variables.


### okerrmod utility
okerrmod is script to perform different local checks (such as free disk space, mysql running, load average, etc.). After initial `okerrmod --init`, few basic check modules 
are enabled.

List all available check modules (`+` - module enabled, `-` - module disabled ):
```shell
$ okerrmod --list
+ backups 0.1 Check freshness for backup files
+ df 0.1 Free disk space
...
```

To run enabled checks just run `okerrmod` without any other commands:
```shell
xenon@braconnier:~$ sudo okerrmod 
okerr updated (200 OK) braconnier:maxfilesz@okerr = 9077814
okerr updated (200 OK) braconnier:apache@okerr = 0
okerr updated (200 OK) braconnier:nonempty@okerr = 0
okerr updated (200 OK) braconnier:empty@okerr = 0
...
```

To run just one check:
```shell
$ sudo okerrmod --run ok
okerr updated (200 OK) braconnier:ok@okerr = OK
```

To enable new check:
```shell
$ sudo okerrmod --enable runstatus
2020/01/17 16:12:30 enable /usr/local/lib/python3.7/dist-packages/okerrupdate/mods-available/runstatus
2020/01/17 16:12:30 make default config file: /etc/okerr/mods-env/runstatus

```

After this, you may want to edit default configuration for this check
```shell
sudo vim /etc/okerr/mods-env/runstatus
```

After this, `okerrmod` will run this check.

To create your own very basic check 'my' create dir `/etc/okerr/mods-available/my` and edit `/etc/okerr/mods-available/my/check`:
```shell
#!/usr/bin/python3
print("STATUS: OK")
```
or if you prefer shell (check is any executable file):
```shell
#!/bin/sh
echo STATUS: OK
```

Now you can run it manually `okerrmod --run my`, enable `okerrmod --enable my`, make/edit config file for it 
`/etc/okerr/mods-env/my`.

## Using okerrupdate python library
Simplest case:
```python
#!/usr/bin/python
import okerrupdate

op = okerrupdate.OkerrProject('MyTextID', secret='MySecret')
i = op.indicator('temp', method='numerical|maxlim=37', policy='Daily')
i.update('36.6')
```

## Documentation 
More info in [okerrupdate documentation](https://okerrupdate.readthedocs.io/).

# Other okerr resources
- [Okerr main website](https://okerr.com/)
- [Okerr-server source code repository](https://github.com/yaroslaff/okerr-dev/) 
- [Okerr client (okerrupdate) repositoty](https://github.com/yaroslaff/okerrupdate) and [okerrupdate documentation](https://okerrupdate.readthedocs.io/)
- [Okerrbench network server benchmark](https://github.com/yaroslaff/okerrbench)
- [Okerr custom status page](https://github.com/yaroslaff/okerr-status)
- [Okerr JS-powered static status page](https://github.com/yaroslaff/okerrstatusjs)
- [Okerr network sensor](https://github.com/yaroslaff/sensor)

