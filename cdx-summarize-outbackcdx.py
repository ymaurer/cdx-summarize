#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import urllib
import importlib
import CdxParser
import requests
cdxsummarize = importlib.import_module('cdx-summarize')
ftype = CdxParser.FORMAT_CDXNbamskrMSVg

def read_url(args, url):
    parser = CdxParser.CdxParser(ftype, args.monthly, args.fullhost)
    aggregate_by = ''
    with requests.get(url, stream=True) as r:
        for line in r.iter_lines(decode_unicode=True):
            res = parser.parse_line(line)
            cdxsummarize.summarize_line(res)
            if args.assume_unique:
                if 'agg' in res and res['agg'] != aggregate_by and aggregate_by != '':
                    cdxsummarize.output_partial_results(args, aggregate_by)
                    aggregate_by = res['agg']

def get_collections(args):
    r = requests.get(args.url + '/api/collections')
    for m in r.json():
        read_url(args, args.url + '/' + m + '?url=&matchType=range')
    cdxsummarize.output_results(args)

def dowork(args):
    get_collections(args)

if __name__ == '__main__':
    parser = ArgumentParser(description='Summarize OutbackCDX index with all collections to JSONL')
    parser.add_argument('--monthly', action="store_true", help='break up statistics into monthly buckets instead of yearly')
    parser.add_argument('--compact', action="store_true", help='do not output fields that are 0')
    parser.add_argument('--fullhost', action="store_true", default=False, help='aggregate by full hostname instead of second level domain')
    parser.add_argument('--assume_unique', action="store_true", default=False, help='assume aggregation entry only appears in a continous run in the CDX file(s) (OK for single, sorted CDX with --fullhost)')
    parser.add_argument('url', action="store", default='http://localhost:8084', help='url of OutbackCDX server')
    args = parser.parse_args()
    dowork(args)