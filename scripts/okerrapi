#!/usr/bin/env python3

import argparse
import sys
import os

import requests
from okerrupdate import __version__, OkerrProject, OkerrExc, get_okerr_conf_dir
from dotenv import load_dotenv

def api_indicators(p, prefix=None):    
    print(p.api_indicators(prefix))

def api_indicator(p, name):
    try:
        print(p.api_indicator(name))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("Not found indicator {name!r} in project {textid!r}".format(name=name, textid=p.textid), file=sys.stderr)
            return 1
        else:
            print(e, file=sys.stderr)


def api_filter(p, *args):
    print(p.api_filter(*args))

def api_set(p, name, *args):
    try:
        print(p.api_set(name, *args))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("Not found indicator {name!r} in project {textid!r}".format(name=name, textid=p.textid), file=sys.stderr)
            return 1
        else:
            print(e, file=sys.stderr)


def get_args():

    conf_file = os.path.join(get_okerr_conf_dir('/etc/okerr'), 'okerrupdate')
    load_dotenv(dotenv_path = conf_file)

    def_api_key = os.getenv('OKERR_API_KEY')
    def_textid = os.getenv('OKERR_TEXTID')

    epilog='''Examples:
    
    # get indicators, explicitly give textid and API-KEY
    okerrapi -i textid -k MY-PROJECT-API-KEY indicators

    # get list of indicators, textid and API-KEY taken from env or /etc/okerr/okerrupdate 
    okerrapi indicators

    okerrapi indicators prefix:

    # get info about particular indicator (-n)
    okerrapi -n srv1:myindicator indicator

    # list indicators matching by filter (status=OK, has tag 'sslcert', host option is 'okerr.com')
    okerrapi filter sslcert OK host=okerr.com

    # set parameter days=20 and retest for indicator (-n)
    okerrapi -n sslcert:okerr.com set days=20 retest=1
    '''

    parser = argparse.ArgumentParser(description='okerr API client {}'.format(__version__), 
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog)
    parser.add_argument('cmd', metavar='COMMAND', help='API command')
    parser.add_argument('args', metavar='ARG', nargs='*', help='argument(s)')
    parser.add_argument('-i', '--textid', metavar='TextID', help='project TextID',
                        default=def_textid)
    parser.add_argument('-n', '--name', metavar='INDICATOR', help='name of indicator',
                        default=None)
    parser.add_argument('-k', '--key', metavar='API-KEY', help='project API-key (from config or $OKERR_API_KEY)',
                        default=def_api_key)
    parser.add_argument('--url', metavar='URL', help='URL of server (usually not needed)', default=None)
    parser.add_argument('--direct', action='store_true', help='Do not use director feature, use direct --url',
                        default=None)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose mode')
    return parser.parse_args()

def main():
    args = get_args()
    p = OkerrProject(args.textid, url=args.url, direct=args.direct, apikey = args.key)
    if args.verbose:
        p.verbose()

    # sanity check
    if args.cmd in ['indicator', 'set'] and not args.name:
        print("Need indicator name (-n)", file=sys.stderr)
        return

    if args.cmd == 'indicators':
        if args.args:
            api_indicators(p, args.args[0])
        else:
            api_indicators(p)

    elif args.cmd == 'indicator':
        api_indicator(p, args.name)

    elif args.cmd == 'filter':
        api_filter(p, *args.args)

    elif args.cmd == 'set':
        d = dict()
        try:
            for arg in args.args:
                k, v = arg.split('=', maxsplit=1)
                d[k] = v
        except ValueError:
            print("Specify arguments as key=value", file=sys.stderr)
            return 1        
        api_set(p, args.name, d)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except OkerrExc as e:
        print(e, file=sys.stderr)
        print("Documentation: https://okerrupdate.readthedocs.io/en/latest/")
        print("Configuration: https://okerrupdate.readthedocs.io/en/latest/configuration.html")
        sys.exit(1)