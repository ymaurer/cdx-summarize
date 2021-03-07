#!/usr/bin/python3
from argparse import ArgumentParser

import sys
import gzip
import json
import requests
import mime_counter

def print_to_stderr(*a): 
	print(*a, file = sys.stderr)

def summarize_tld(tld, metadata, args):
    for y in metadata["urls"]:
        out = mime_counter.init_counter()
        for m in metadata["urls"][y]:
            mime_counter.add_mime(out, m, metadata["urls"][y][m])
            if y in metadata["urls_total_compressed_size"] and m in metadata["urls_total_compressed_size"][y]:
                mime_counter.add_mime(out, m, 0, metadata["urls_total_compressed_size"][y][m])
        formatted = mime_counter.as_dict(out)
        formatted["date"] = y+'-01-01'
        formatted["tld"] = tld
        formatted["source"] = args.source
        formatted["webarchive"] = args.webarchive
        print('{"index":{"_index":"'+args.index+'"}}')
        print(json.dumps(formatted))

def dowork(args):
    for tld in args.tld:
        if args.proxy:
            print(args.murl + tld)
            r = requests.get(args.murl + tld, proxies={'http':args.proxy,'https':args.proxy})
        else:    
            r = requests.get(args.murl + tld)
        try:
            d = r.json()
        except Exception as inst:
            print_to_stderr("Unexpected error:", inst, args.murl, tld)
        summarize_tld(tld, d, args)

parser = ArgumentParser(description='Download metadata about a TLD from the internet archive, summarize the mime types and put it into a format to load into elasticsearch')
parser.add_argument('-index', required=False, default='cdx-metadata', help='elasticsearch index name')
parser.add_argument('-proxy', required=False, help='https proxy in the format http://x.x.x:8000')
parser.add_argument('-murl', required=False, default='https://web.archive.org/__wb/search/metadata?q=tld:', help='metadata query url')
parser.add_argument('-source', required=False, default='ia-metadata', help='source identifier')
parser.add_argument('-webarchive', required=False, default='archive-org', help='webarchive identifier')
parser.add_argument('tld', nargs='*', help='tld name (can be several)')

args = parser.parse_args()
dowork(args)
