# okerrupdate - client-side okerr module and utilities

## Installation 

```shell
sudo pip3 install okerrupdate
sudo okerrmod --init # enable few basic modules, create /etc/cron.d/ job, create basic config template
sudo vim /etc/okerr/okerrupdate
```

and modify okerrupdate file:
~~~
OKERR_TEXTID=MyTextID
OKERR_SECRET=MySecret

OKERR_MOD_AVAIL=
~~~

## Basic usage

### okerrupdate utility

okerrupdate is small script which updates/creates indicators in okerr project. 

This will create simplest indicator 'myindicator' with all default settings (type 'heartbeat', policy 'Default').
Indicator will send alert if it will be updated to 'ERR' or if will not be updated for some time 
(Default policy period+patience).
~~~
$ okerrupdate myindicator OK
okerr updated (200 OK) myindicator@okerr = OK
~~~

This will create numerical indicator 'temp' with current value 36.6, and policy 'Daily'. Will send alert if not updated 
for a day or if value will be over maxlim (37).
~~~
$ okerrupdate -p Daily -m 'numerical|maxlim=37' temp 36.6
okerr updated (200 OK) temp@okerr = 36.6
~~~ 

Project TextID and secret is read from `/etc/okerr/okerrupdate` file or `OKERR_TEXTID` and `OKERR_SECRET` environment 
variables.


### okerrmod utility
okerrmod is script to use different okerr checks. After initial `okerrmod --init`, few basic simple check modules 
are enabled.

List all available check modules:
~~~
$ okerrmod --list
+ backups 0.1 Check freshness for backup files
+ df 0.1 Free disk space
...
~~~

To run enabled checks just run `okerrmod` without any other commands:
~~~
xenon@braconnier:~$ sudo okerrmod 
okerr updated (200 OK) braconnier:maxfilesz@okerr = 9077814
okerr updated (200 OK) braconnier:apache@okerr = 0
okerr updated (200 OK) braconnier:nonempty@okerr = 0
okerr updated (200 OK) braconnier:empty@okerr = 0
...
~~~

To run just one check:
~~~
$ sudo okerrmod --run ok
okerr updated (200 OK) braconnier:ok@okerr = OK
~~~

To enable new check:
~~~
$ sudo okerrmod --enable sql
2020/01/17 18:46:58 enable /home/xenon/repo/okerrupdate/okerrupdate/mods-available/sql
~~~

After this, you may want to edit default configuration for this check
~~~
sudo vim /etc/okerr/mods-env/sql
~~~

After this, `okerrmod` will run this check.

To create your own very basic check 'my' create dir `/etc/okerr/mods-available/my` and edit `/etc/okerr/mods-available/my/check`:
~~~
#!/usr/bin/python3
print("STATUS: OK")
~~~
or if you prefer shell (check is any executable file):
~~~
#!/bin/sh
echo STATUS: OK
~~~

Now you can run it manually `okerrmod --run my`, enable `okerrmod --enable my`, make/edit config file for it 
`/etc/okerr/mods-env/my`.

More info in [okerrupdate wiki](https://gitlab.com/yaroslaff/okerrupdate/-/wikis/home).


## Using okerrupdate python library
Simplest case:
~~~
#!/usr/bin/python
import okerrupdate

op = okerrupdate.OkerrProject('MyTextID', secret='MySecret')
i = op.indicator('temp', method='numerical|maxlim=37', policy='Daily')
i.update('36.6')
~~~
