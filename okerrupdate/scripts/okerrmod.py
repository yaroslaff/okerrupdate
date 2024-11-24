#!/usr/bin/python3
import okerrupdate
from okerrupdate import OkerrExc
import argparse
import socket
import subprocess
import os
import shutil
import sys
import logging
import glob
import random
from dotenv import load_dotenv

okerr_conf_dir = okerrupdate.get_okerr_conf_dir(default='/etc/okerr')

def_mods_enabled = os.path.join(okerr_conf_dir, 'mods-enabled')

def_mods_available = [
    os.path.join(okerr_conf_dir, 'mods-available'),
    os.path.join(os.path.dirname(okerrupdate.__file__), 'mods-available')
    ]

def_env = os.path.join(okerr_conf_dir, 'mods-env')
log = None

class OkerrmodException(Exception):
    pass

class NoModule(OkerrmodException):
    pass

class NotConfigured(OkerrmodException):
    pass

def decode_escaped(s):
    return s


def parse_dotenv(dotenv_path):
    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)

            # Remove any leading and trailing spaces in key, value
            k, v = k.strip(), v.strip()
            if len(v) > 0:
                quoted = v[0] == v[len(v) - 1] in ['"', "'"]

                if quoted:
                    v = decode_escaped(v[1:-1])

            yield k, v


class StrAttr:
    def __init__(self, s=None):
        self._keys = list()
        self.comment = '#'
        if s:
            self.loads(s)


    def loads(self, s):
        if isinstance(s, bytes):
            s = s.decode('utf-8')

        for line in str(s).split('\n'):
            if not line:
                continue
            if self.comment and line.startswith(self.comment):
                continue
            k, v = line.split(':', 1)
            v = v.strip()
            self.set(k, v)

    def set(self, k, v):
        setattr(self, k, v)
        self._keys.append(k)

    def __repr__(self):
        s = ""
        for k in self._keys:
            s += '{}={} '.format(k, getattr(self, k))
        return s


class UpdateStrAttr(StrAttr):
    def __init__(self, s=None, name='noname'):
        self.METHOD = 'heartbeat'
        self.NAME = name
        self.STATUS = None
        self.DETAILS = ''
        self.POLICY = 'Default'
        self.TAGS = ''
        super().__init__(s)


class InfoStrAttr(StrAttr):
    def __init__(self, s=None):
        super().__init__(s)
        self.Version = ''
        self._keys.append('Version')
        self.Description = ''
        self._keys.append('Description')


class Module:
    def __init__(self, mod_path):

        if mod_path is None:
            raise NoModule('No such module: {}'.format(mod_path))

        self.path_enabled = def_mods_enabled
        self.path_available = def_mods_available
        self.path_env = def_env

        if mod_path.endswith('/'):
            mod_path = mod_path[:-1]

        if not os.path.isdir(mod_path) or not os.path.isfile(os.path.join(mod_path, 'check')):
            raise ValueError('No module {} found'.format(mod_path))

        # out_info = subprocess.run([path, 'info'], stdout = subprocess.PIPE)
        info_path = os.path.join(mod_path, '_info')
        self.info = InfoStrAttr()
        if os.path.isfile(info_path):
            with open(info_path) as fh:
                self.info.loads(fh.read())

        self._name = os.path.basename(mod_path)
        self._path = os.path.realpath(mod_path)

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @staticmethod
    def find_module(modspec):
        """

        :param modspec: name of module or path to module
        :return: path to module

        may raise NotConfigured
        """
        if not os.path.isdir(def_mods_enabled):
            raise NotConfigured('Dir {dir} not exists. Maybe forgot to run okerrmod --init?'
                .format(dir=def_mods_enabled))

        for path in list_dirs([def_mods_enabled, def_mods_available]):
            if os.path.basename(path) == modspec:
                return path
            
        if os.path.isdir(modspec):
            path = modspec
            return path

    def load_env(self):
        env = dict()
        envfile = os.path.join(self.path_env, self._name)
        if not os.path.isfile(envfile):
            log.debug('no envfile {} for mod {!r}, using system env'.format(envfile, self._name))
            env = dict(os.environ)
            return env

        log.debug("load env for {} from {}".format(self._name, envfile))
        env = dict(parse_dotenv(envfile))
        return env

    def check(self, prefix, project, secret=None, dump=False):

        env = self.load_env()

        env['PREFIX'] = prefix + env.get('PREFIX2', '')
        env['BASENAME'] = self._name
        env['VERSION'] = okerrupdate.__version__

        path_check = self.mod_file('check')

        log.debug('... Run check {}'.format(path_check))
        out_info = subprocess.run([sys.executable, path_check, self.name], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, env=env)

        if out_info.stderr:
            log.error("CHECK ERR: {}".format(out_info.stderr.decode('utf-8')))

        if dump:
            print(out_info.stdout.decode('utf8'))
            return

        for update in out_info.stdout.decode('utf8').split('\n\n'):
            if not update:
                # skip empty
                continue
            u = UpdateStrAttr()
            u.set('POLICY', env.get('POLICY'))
            u.set('NAME', prefix+self._name)
            try:
                u.loads(update)
            except ValueError:
                log.error("Failed to parse {!r} from {}".format(update, self._path))

            log.debug(u)
            if u.STATUS is not None:
                i = project.indicator(u.NAME, secret=secret,
                                      method=u.METHOD, policy=u.POLICY, tags=u.TAGS.split(' '))
                try:
                    i.update(u.STATUS, details=u.DETAILS)
                except okerrupdate.OkerrExc as e:
                    log.error('Failed to update {name} = {status} exception: {exc}'
                        .format(name = u.NAME, status = u.STATUS, exc=e))

    def enabled(self):
        for basename in os.listdir(self.path_enabled):
            path = os.path.join(self.path_enabled, basename)
            if os.path.realpath(path) == self._path:
                return True

        return False

    def has_method(self, method):
        path_method = os.path.join(self._path, method)
        return os.path.isfile(path_method)

    def mod_file(self, file):
        return os.path.join(self._path, file)

    def has_file(self, file):
        return os.path.isfile(self.mod_file(file))

    def enable(self):
        log.info("enable {}".format(self._path))
        envfile = os.path.join(self.path_env, self._name)

        if self.has_method('preenable'):
            s = subprocess.run([self.mod_file('preenable')], stdout=subprocess.PIPE)
            if s.returncode:
                log.error(s.stdout.decode().strip())
                log.error("Pre-enable check failed.")
                return

        if self.has_file('_config'):
            if not os.path.exists(envfile):
                log.info("make default config file: {}".format(envfile))
                shutil.copy(self.mod_file('_config'), envfile)
            else:
                log.info("already exists config file: {}".format(envfile))

        link_path = os.path.join(self.path_enabled, self._name)

        if os.path.exists(link_path):
            log.warning('Already exists {} -> {}'.format(link_path, os.path.realpath(link_path)))
            return

        os.symlink(self._path, link_path)

    def disable(self):
        log.info("disable {}".format(self._path))
        path = os.path.join(self.path_enabled, self._name)
        if os.path.exists(path):
            log.debug("disable {}".format(path))
            os.unlink(path)
        else:
            log.info('not enabled {}'.format(self._path))

    def __repr__(self):
        if self.enabled():
            sign = '+'
        else:
            sign = '-'
        return "{} {}: {}".format(sign, self._name, self.info.Description)

def list2str(li):
    """

    :param li:  list of strings or list of lists
    :return:  strings from lists
    """
    for e in li:
        if isinstance(e, str):
            yield e
        else:
            for ee in list2str(e):
                yield ee


def list_dirs(dirs):
    for d in list2str(dirs):
        for basename in os.listdir(d):
            path = os.path.join(d, basename)
            yield path


def uniq(iterable):
    last = None
    for e in iterable:
        if e == last:
            continue
        last = e
        yield e

def read_template(path:str , tokens: dict):
    with open(path, "r") as srcf:
        data = srcf.read()
        for token, value in tokens.items():
            data = data.replace(token, value)
        return data


def main():
    global log
    global def_mods_available

    # main code
    conf_file = os.path.join(okerr_conf_dir, 'okerrupdate')

    load_dotenv(dotenv_path=conf_file)

    def_prefix = os.getenv('PREFIX', socket.gethostname().split('.')[0]+':')
    def_secret = os.getenv('OKERR_SECRET', None)
    def_textid = os.getenv('OKERR_TEXTID', None)
    def_direct = bool(int(os.getenv('OKERR_DIRECT','0')))
    def_url = os.getenv('OKERR_URL', None)

    parser = argparse.ArgumentParser(description='okerr module manager {}'.format(okerrupdate.__version__))
    parser.add_argument(metavar='MODULE', dest='modlist', nargs='*',
                        help='module(s) by name or mod directory (wildcard)',
                        default=glob.glob(os.path.join(def_mods_enabled,'*')))
    parser.add_argument('-p', '--prefix', metavar='PREFIX', default=def_prefix, nargs='?',
                        help='prefix for indicator. default: {}'.format(def_prefix))
    parser.add_argument('-i', '--textid', metavar='TextID', default=def_textid,
                        help='Project textid ({!r})'.format(def_textid))
    parser.add_argument('--url', metavar='URL', help='URL of server (usually not needed)', default=def_url)
    parser.add_argument('--direct', action='store_true',
                        help='Do not use director feature, use direct --url', default=def_direct)
    parser.add_argument('-S', '--secret', metavar='SECRET', help='SECRET', default=def_secret)
    # Policy not actual here, because different mods may need different policies
    # parser.add_argument('-p','--policy', metavar='POLICY', help='use this policy by default ', default='Default')
    parser.add_argument('-v', dest='verbose', action='count', help='verbose', default=0)
    parser.add_argument('-q', dest='quiet', action='store_true', help='quiet', default=False)
    parser.add_argument('--log', metavar='PATH', help='log filename', default=None)
    parser.add_argument('--dry', default=False, action='store_true', help='Dry run, do not update any indicator')
    parser.add_argument('--dump', default=False, action='store_true', help='dump output from module, do not process it')
    parser.add_argument('--avail', default=os.getenv('OKERR_MOD_AVAIL', None),
                   help='Additional path to other mods-available ({})'.format(os.getenv('OKERR_MOD_AVAIL')))

    g = parser.add_argument_group('Commands')
    g.add_argument('--enable', default=False, action='store_true', help='Enable modules')
    g.add_argument('--disable', default=False, action='store_true', help='Disable module')
    g.add_argument('--list', default=False, action='store_true', help='List modules')
    g.add_argument('--init', default=False, action='store_true', help='Init /etc/okerr directory')
    g.add_argument('--clone', nargs=2, metavar=('CHECK', 'NEW_NAME'), help='Clone check with other name')
    g.add_argument('--version', default=False, action='store_true', help='Show only package version')

    args = parser.parse_args()

    if args.version:
        print(okerrupdate.__version__)
        return

    if args.verbose:
        print("Using config file", conf_file)

    if args.avail:
        def_mods_available = [args.avail] + def_mods_available


    logging.basicConfig()
    log = logging.getLogger('okerrmod')
    log.propagate = False

    oulog = logging.getLogger('okerrupdate')

    # log.removeHandler(log.handlers[0])
    out = logging.StreamHandler(sys.stdout)
    out.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    out.setLevel(logging.DEBUG)
    log.addHandler(out)

    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)
    else:
        log.setLevel(logging.INFO)

    if args.clone:
        src = args.clone[0]
        dst = args.clone[1]

        # clone symlink
        src_link = os.path.join(def_mods_enabled, src)
        src_target = os.path.realpath(src_link)
        clone_link = os.path.join(def_mods_enabled, dst)
        os.symlink(src_target, clone_link)

        # copy config
        src_config = os.path.join(def_env, src)
        dst_config = os.path.join(def_env, dst)
        shutil.copy(src_config, dst_config)

        print("Cloned {} as check {}".format(src_target, dst))
        print("Config: {}".format(dst_config))

        sys.exit()

    if args.list:
        listed = list()
        for path in uniq(sorted(list_dirs([def_mods_enabled, def_mods_available]))):
            if not os.path.isdir(path):
                continue
            m = Module(path)
            if m.path in listed:
                continue
            print(m)
            listed.append(m.path)
        sys.exit()

    if args.enable:
        for modspec in args.modlist:
            try:
                modpath = Module.find_module(modspec)
                print("modpath:", modpath)
                m = Module(modpath)
            except (ValueError, OkerrmodException) as e:
                log.error(e)
            else:
                m.enable()
        sys.exit()

    if args.disable:
        for modspec in args.modlist:
            modpath = Module.find_module(modspec)
            try:
                m = Module(modpath)
            except (ValueError, NoModule) as e:
                log.error(e)
            else:
                m.disable()
        sys.exit()

    if args.init:

        if not os.getuid() == 0:
            log.error("You must be root to --init and make /etc/okerr")
            exit(1)

        dirs = ['/etc/okerr', '/etc/okerr/mods-available', '/etc/okerr/mods-enabled', '/etc/okerr/mods-env/']
        mods = ['la', 'opentcp', 'df']

        for dirname in dirs:
            if not os.path.isdir(dirname):
                log.info("Create {}".format(dirname))
                os.mkdir(dirname)
            else:
                log.info('.. already exists {}'.format(dirname))

        if not os.path.isfile(conf_file):
            with open(conf_file, 'w') as fh:
                fh.write("""
# Stub for okerrmod            
PREFIX={prefix}
OKERR_TEXTID={textid}
OKERR_SECRET={secret}
OKERR_URL={url}
OKERR_DIRECT={direct}

OKERR_MOD_AVAIL=
""".lstrip().format(prefix=args.prefix,
                    textid=args.textid or '',
                    secret=args.secret or '',
                    url=args.url or '',
                    direct=1 if args.direct else 0
                ))

        for mod_spec in mods:
            mod_path = Module.find_module(mod_spec)
            m = Module(mod_path)
            m.enable()

        if os.path.exists('/etc/cron.d/'):
            offset = random.randrange(20)
            tokens = {
                '%ARGV0%': sys.argv[0],
                '%PYTHON%': sys.executable,
                '%OKERRMOD%': os.path.realpath(__file__),
                '%MINUTES%': ','.join(map(str, [offset, offset+20, offset+40]))
            }

            crondata = read_template(os.path.join(os.path.dirname(okerrupdate.__file__), 'contrib', 'okerrmod'), tokens)

            cronjob = '/etc/cron.d/okerrmod'
            if not os.path.exists(cronjob):
                with open(cronjob, 'w') as fh:
                    print("Generate", cronjob)
                    fh.write(crondata)
        else:
            print("Did not created /etc/cron.d/okerrmod because no /etc/cron.d/")

        exit()

    if args.log:
        fh = logging.FileHandler(args.log)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S'))
        log.addHandler(fh)
        oulog.addHandler(fh)

    # if we're here: run
    p = okerrupdate.OkerrProject(args.textid, url=args.url, direct=args.direct, dry_run=args.dry)
    if args.verbose >= 2:
        p.verbose()

    for mod_spec in args.modlist:
        try:
            mod_path = Module.find_module(mod_spec)
        except NotConfigured as e:
            print(e, file=sys.stderr)
            continue

        if mod_path is None:
            log.error('No module: {}'.format(mod_spec))
            continue
        m = Module(mod_path=mod_path)
        m.check(prefix=args.prefix, project=p, secret=args.secret, dump=args.dump)


if __name__ == '__main__':
    try:
            main()
    except OkerrExc as e:
        print(e, file=sys.stderr)
        print("Documentation: https://okerrupdate.readthedocs.io/en/latest/")
        print("Configuration: https://okerrupdate.readthedocs.io/en/latest/configuration.html")
        sys.exit(1)
