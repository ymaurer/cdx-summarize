#!/usr/bin/python3

from argparse import ArgumentParser
import sys
import json
import mime_counter
import operator
from publicsuffixlist import PublicSuffixList

Hosts = dict()

def print_to_stderr(*a):
    print(*a, file = sys.stderr)

def simplifyhost(psl, args, host):
    if args.aggregatehosts == 'lvl2':
        p = host.rfind('.')
        if p > -1:
            p1 = host.rfind('.', 0, p -1)
            return host[p1+1:]
    elif args.aggregatehosts == 'publicsuffixlist':
        retval = psl.privatesuffix(host)
        if retval:
            return retval
        else:
            return host
    return host

def addFile(args, filename, psl):
    f = open(filename, 'r', errors="ignore")
    for line in f:
        p = line.find(" {\"")
        host = line[0:p]
        if args.aggregatehosts != 'none':
            host = simplifyhost(psl, args, host)
        entry = json.loads(line[p+1:])
        if not host in Hosts:
            Hosts[host] = dict()
        for year, values in entry.items():
            varr = mime_counter.from_dict(values)
            if args.yearly:
                year = year[0:4]
            if year in Hosts[host]:
                for i, vi in enumerate(varr):
                    Hosts[host][year][i] += vi
            else:
                Hosts[host][year] = varr

def outputResults(args):
    dict_items = Hosts.items()
    sorted_items = sorted(dict_items)
    for lvl2, entry in sorted_items:
        r = {}
        for year, values in entry.items():
            if args.compact:
                tmp = mime_counter.as_dict(values)
                r[year] = {}
                for k in tmp:
                    if tmp[k] > 0:
                        r[year][k] = tmp[k]
            else:
                r[year] = mime_counter.as_dict(values)
        print(lvl2, json.dumps(r))

def output_host(args, hostname, years):
    r = {}
    for year, values in years.items():
        if args.compact:
            tmp = mime_counter.as_dict(values)
            r[year] = {}
            for k in tmp:
                if tmp[k] > 0:
                    r[year][k] = tmp[k]
        else:
            r[year] = mime_counter.as_dict(values)
    print(hostname, json.dumps(r))

# assume input files are sorted by aggregation key (host)
# open all files at once and then advance in each file only if its key is the smallest
def read_sorted(args):
    if args.aggregatehosts and args.aggregatehosts != 'none':
        print_to_stderr('ERROR: incompatible arguments: --aggregatehosts', args.aggregatehosts,'and --assume_unique')
        quit()
    fil = []
    # open all files
    nEOF = 0
    for f in args.file:
        obj = {'file':f, 'fp': open(f, 'r', errors="ignore")}
        line = obj['fp'].readline()
        if line == '':
            obj['eof'] = 'Z'
            nEOF+=1
            obj['host']=''
        else:
            obj['eof'] = 'A'
            p = line.find(" {\"")
            obj['host'] = line[0:p]
            obj['years'] = json.loads(line[p+1:])
        fil.append(obj)
    fil.sort(key=lambda x:x['eof']+x['host'])
    d = {}
    lasthost = ''
    while nEOF < len(fil):
        h = fil[0]['host']
        if h != lasthost:
            if lasthost != '':
                output_host(args, lasthost, d)
                d = {}
            lasthost = h
        for year, values in fil[0]['years'].items():
            varr = mime_counter.from_dict(values)
            if args.yearly:
                year = year[0:4]
            if year in d:
                for i, vi in enumerate(varr):
                    d[year][i] += vi
            else:
                d[year] = varr
        line = fil[0]['fp'].readline()
        if line == '':
            fil[0]['eof'] = 'Z'
            nEOF+=1
        else:
            p = line.find(" {\"")
            fil[0]['host'] = line[0:p]
            fil[0]['years'] = json.loads(line[p+1:])
        fil.sort(key=lambda x:x['eof']+x['host'])
    if lasthost != '':
        output_host(args, lasthost, d)
    # close all files
    for o in fil:
        o['fp'].close()

def dowork(args):
    if args.assume_unique:
        read_sorted(args)
    else:
        if args.aggregatehosts == 'publicsuffixlist':
            psl = PublicSuffixList()
        else:
            psl = None
        for f in args.file:
            try:
                addFile(args, f, psl)
            except Exception as inst:
                print_to_stderr("Error", inst, f)
        outputResults(args)

parser = ArgumentParser(description='Combine summary files generated by cdx-summary.py')
parser.add_argument('--yearly', action="store_true", help='force output into yearly buckets')
parser.add_argument('--compact', action="store_true", help='do not output fields that are 0')
parser.add_argument('--aggregatehosts', choices=['none','lvl2', 'publicsuffixlist'], help='Aggregate hosts (incompatible with --assume_unique when full hosts are in the input file)')
parser.add_argument('--assume_unique', action="store_true", default=False, help='assume aggregation entry only appears in a continous run in the CDX file(s)')
parser.add_argument('file', nargs='*', help='summary file (can be several)')

args = parser.parse_args()
dowork(args)
