import time
import requests
import logging
import re
import time
import sys
import os

from urllib.parse import urlparse, urljoin


class OkerrExc(Exception):
    pass

class OkerrIndicator:
    def __init__(self, name, project, secret=None, method=None, policy=None, desc=None, tags=None, error=None, origkeypath=None, keypath=None):
    
        if not isinstance(project, OkerrProject):
            project = OkerrProject(project)
            
        self.name = name
        self.project = project
        self.secret = secret
        self.method = method
        self.policy = policy
        self.tags = tags
        self.error = error
        self.origkeypath = origkeypath
        self.keypath = keypath
        self.desc = desc
        
        self.lastupdate = 0
        self.throttle = 300
        self.last_status = None

    def update(self, status, details=None):
        def skip(self, status):
            if time.time() < self.lastupdate + self.throttle:
                # premature
                if self.method == 'numerical':
                    # always skip premature numerical updats
                    return True
                else:
                    # other methods, skip if same status
                    if status == self.last_status:
                        return True
            return False
        
        if skip(self, status):
            self.project.log.debug('skip update {}@{}'.format(self.name, self.project.textid))
            return True # success if skipped
        
        success = self.project.update(self.name, status = status, details = details, secret = self.secret, method = self.method, 
            policy = self.policy, tags = self.tags, error = self.error, desc=self.desc, origkeypath = self.origkeypath, keypath = self.keypath)
        self.lastupdate = time.time()
        self.last_status = status
        
        return success
        
    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "{}@{}".format(self.name, self.project)


class OkerrProject:
    
    url = None # base url, for director
    project_url = None
    
    def __init__(self, textid=None, secret=None, url=None, dry_run=False, direct=False, config=None):
        self.textid = textid or os.getenv('OKERR_TEXTID')
        self.url = url
        self.dry_run = dry_run
        self.secret = secret or os.getenv('OKERR_SECRET')
        self.url_expiration = 300
        self.direct = direct
        self.x = dict()
        if url:
            self.url = url
        else:
            self.url = 'https://cp.okerr.com/' 

        self.make_logger()

        if self.textid is None or self.secret is None:
            # try read okerrclient.conf
            self.read_config(config)

    def make_logger(self):
        logging.basicConfig()
        self.log = logging.getLogger('okerrupdate')
        if len(self.log.handlers) == 0:
            # log.removeHandler(log.handlers[0])
            out = logging.StreamHandler(sys.stdout)
            out.setFormatter(logging.Formatter('%(message)s'))
            out.setLevel(logging.DEBUG)
            self.log.addHandler(out)
        self.log.setLevel(logging.INFO)
        self.log.propagate = False

    def read_config(self, filename=None):
        if not filename:
            filename = '/etc/okerrclient.conf'

        try:
            with open(filename) as f:
                for line in f:
                    line = line.split('#')[0]
                    try:
                        k,v = line.split('=',1)
                        k = k.strip(' \n')
                        v = v.strip(' \n')
                        if k in ['textid', 'secret']:
                            setattr(self, k, v)
                    except ValueError:
                        pass
        except IOError as e:
            self.log.warning('cannot read config {}'.format(filename))
            pass

    def setloglevel(self,lvl):
        self.log.setLevel(lvl)
        
    def verbose(self):
        self.setloglevel(logging.DEBUG)

    def setlog(self, log):
        self.log = log

    def indicator(self, name, secret=None, desc=None, method=None, policy=None, tags=None, error=None, origkeypath=None, keypath=None):

        if secret is None:
            secret = self.secret

        desc = desc or ''

        i = OkerrIndicator(name, self, secret = secret, method = method, desc = desc, policy = policy,
            tags = tags, error = error, origkeypath = origkeypath, keypath = keypath)
        return i

    def update(self,name, status, details=None, secret=None, desc=None,
        method=None, policy='Default', tags=None, error=None, origkeypath=None, keypath=None):
        if self.dry_run:
            self.log.debug('Do NOT update: dry run. {} = {}'.format(name, repr(status)))            
            return

        textid = self.textid
        tags = tags or list()
        secret = secret or self.secret
        fullname = '{}@{}'.format(name, self.textid)
        desc = desc or ''
        
        if not textid:
            self.log.error('Do not update {} no textid'.format(name))
            return
        
        # fix name
        if name.startswith(':') and self.prefix is not None:
            name = self.prefix+name

        r = None                
        
        url = self.geturl()

        if not url:
            self.log.error("cannot update, url not given!")
            raise OkerrExc('cannot update, url not given')
            return

        if not url.endswith('/'):
            url+='/'
            
        url = url+'update'
        
        self.log.debug("update: {} = {} ({}) url: {}".format(fullname,status,details, url))

        
        if keypath is None:
            keypath=''
            
        if origkeypath is None:
            origkeypath=''


        payload={
            'textid': textid, 
            'name':name, 
            'status': str(status), 
            'details': details, 
            'secret': secret, 
            'method': method,
            'policy': policy, 
            'tags': ','.join(tags),
            'error': error,
            'keypath': keypath, 
            'origkeypath': origkeypath,
            'desc': desc
        }

        # process x
        for k, v in self.x.items():
            xname = "x_" + k
            payload[xname] = v

        if secret:
            secretlog="[secret]"
        else:
            secretlog="[nosecret]"
        start = time.time()
        
        
        preview = str(status)
        
        preview = re.sub('[\r\n]'," ", preview)
        
        if len(str(preview))>40:
            preview = str(preview)[:38]+".."
        else:
            preview = str(preview)
            
        
        stop = False
        success = False
        
        try:
            r = requests.post(url, data=payload, timeout=5)
            if r.status_code == 200:
                stop = True
                success = True
                self.log.info('okerr updated ({} {}) {} = {}'.\
                    format(r.status_code, r.reason, fullname, preview))
            else:
                self.log.error('okerr update error ({} ({}): {}) {}={} {}'.\
                    format(r.status_code,r.reason, r.text, fullname,preview,secretlog))
        
            self.log.debug('Request to URL {}:'.format(r.request.url))
            self.log.debug(r.request.body)
            
        except requests.exceptions.RequestException as e:
            raise OkerrExc('okerr exception {} {}={} {}'.\
                format(e,fullname,status,secretlog))

        if r:
            self.log.debug(r.content)
        else:
            self.log.debug("no reply, check log")
        self.log.debug("took {} sec.".format(time.time() - start))
    
        return success


    def __repr__(self):
        if self.secret:
            out = '{} [secret]'.format(self.textid)
        else:
            out = '{}'.format(self.textid)
        return out
        
    def __unicode__(self):
        return self.textid        
    
    def need_update_url(self):
        if self.project_url is None:
            # if no url, get it
            return True
        
        if not self.url_expiration:            
            # if never expires - no need
            return False
        
        if (time.time() - self.url_received) > self.url_expiration:
            # expired, renews
            return True
        
        # not expired
        return False

    # OkerrProject.geturl
    def geturl(self):

        if self.direct:
            return self.url

        if self.need_update_url():
            durl = urljoin(self.url,'/api/director/{}'.format(self.textid))
            try:
                r = requests.get(durl, timeout=5)
            except requests.exceptions.RequestException as e:
                self.log.error("ERROR! geturl connection error: {}".format(e))
                self.project_url = None
                self.url_received = 0
                return None                        
            if r.status_code != 200:
                self.log.error("ERROR! status code: {} for dURL {}".format(r.status_code, durl))
                return None

            self.log.debug("got url {} from director {}".format(r.text.rstrip(), durl))
            self.project_url = r.text.rstrip()
            self.url_received = time.time()
        self.log.debug("geturl: return {}".format(self.project_url))
        return self.project_url
