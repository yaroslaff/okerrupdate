# okerrupdate - simple interface to update okerr indicator

## Simplest 

Reads textid and secret from default config file (/etc/okerrclient.conf), updates heartbeat indicator 'test:1' with status OK. If no such indicator - creates it (if policy allows autocreate). 
~~~
#!/usr/bin/python
import okerrupdate
op = okerrupdate.OkerrProject()
i = op.indicator("test:1")
i.update('OK')
~~~

... or in one line, right from shell:
~~~
python -c 'import okerrupdate; okerrupdate.OkerrProject("MyTextID").indicator("qqqq", secret="MySecret").update("OK")'
~~~


## More detailed

Sets verbose mode. Sets textid and secret from script. Creates numerical indicator and sets parameters for it, then updates it.
~~~
#!/usr/bin/python
import okerrupdate

# create okerr project
op = okerrupdate.OkerrProject('MyTextID', 'MySecret1')
op.verbose()

# create indicator
i = op.indicator("test:1", method='numerical|maxlim=37')
i.update('36.6', 'Current temperature is normal')
~~~

# Classes and Methods

## OkerrProject

~~~
def __init__(self, textid=None, secret=None, url=None, dry_run=False, config=None):
~~~

If textid not specified, read_config() method used. 

- textid - project textid
- secret - secret key to update indicators
- url - URL of server (You dont need to use it in most cases)
- dry_run - if True, no indicators will be updated
- config - filename of okerrclient.conf file

~~~
def read_config(self, filename=None):
~~~
Reads textid and secret from config file *filename* (default: /etc/okerrclient.conf). 


~~~
def setloglevel(self,lvl):
    self.log.setLevel(lvl)
        
def verbose(self):
    self.setloglevel(logging.DEBUG)

def setlog(self, log):
    self.log = log
~~~

Can be used to configure logging

~~~
def indicator(self, name, secret=None, method=None, policy=None, tags=None, error=None, origkeypath=None, keypath=None):
~~~
Most important method. Returns OkerrIndicator project with this parameters.

## OkerrIndicator
~~~
def __init__(self, name, project, secret=None, method=None, policy=None, tags=None, error=None, origkeypath=None, keypath=None):
~~~
Usually not used directly, OkerrProject.indicator() will create it.

~~~
def update(self, status, details=None):
~~~
Updates indicator. Raises OkerrExc exception if any problem. Requests exceptions are catched inside method and OkerrExc is raised.

Skips update if less then 300 seconds passed since last update. (So, it's safe to call it in quick loop, it will handle throttling itself)

## OkerrExc
Dummy class for exceptions. Use it to catch any exception. Snippet from okerrupdate code:
~~~
class OkerrExc(Exception):
    pass
~~~

## Examples
~~~
from okerrupdate import OkerrProject, OkerrExc

op = OkerrProject() # textid and secret not specified, will be read from /etc/okerrclient.conf
op.verbose()
i = op.indicator('testindicator', method='numerical|minlim=0|maxlim=100')

try:
    i.update(80)
except OkerrExc as e:
    print("Got OkerrExc: {}".format(e))
~~~

