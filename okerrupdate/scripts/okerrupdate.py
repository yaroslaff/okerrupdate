#!/usr/bin/python3
from okerrupdate import OkerrProject, OkerrExc, __version__
from dotenv import load_dotenv
import argparse
import os
import sys

import okerrupdate

def main():
    conf_file = os.path.join(okerrupdate.get_okerr_conf_dir('/etc/okerr'), 'okerrupdate')
    load_dotenv(dotenv_path = conf_file)

    parser = argparse.ArgumentParser(description='Micro okerr update utility {}'.format(__version__))
    parser.add_argument('name', metavar='INAME', help='name of indicator (name@textid)')
    parser.add_argument('value', metavar='VALUE', help='value')
    parser.add_argument('-i', '--textid', metavar='TextID', help='name of indicator',
                        default=None)
    parser.add_argument('--url', metavar='URL', help='URL of server (usually not needed)', default=None)
    parser.add_argument('--direct', action='store_true', help='Do not use director feature, use direct --url',
                        default=None)
    parser.add_argument('-S', '--secret', metavar='SECRET', help='SECRET', default=None)
    parser.add_argument('-m', '--method', metavar='METHOD', help='method|arg1=val1|arg2=arg2', default='heartbeat')
    parser.add_argument('-p', '--policy', metavar='POLICY', help='policy', default='Default')
    parser.add_argument('--desc', metavar='DESC', help='Description (used only when create indicators)', default='')

    parser.add_argument('-d', '--details', metavar='DETAILS', help='details', default=None)

    parser.add_argument('-v', dest='verbose', action='store_true', help='verbose', default=False)

    args = parser.parse_args()

    # support optional name@textid syntax
    if '@' in args.name:
        name, textid = args.name.split('@')
    else:
        name = args.name
        textid = args.textid    

    p = OkerrProject(textid, url=args.url, direct=args.direct)

    if args.verbose:
        p.verbose()

    try:
        i = p.indicator(name, secret=args.secret, method=args.method, desc=args.desc, policy=args.policy)
        i.update(args.value, details=args.details)

    except OkerrExc as e:
        print(e, file=sys.stderr)
        print("Documentation: https://okerrupdate.readthedocs.io/en/latest/")
        print("Configuration: https://okerrupdate.readthedocs.io/en/latest/configuration.html")
        sys.exit(1)    
