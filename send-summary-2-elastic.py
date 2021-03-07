#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import json
from datetime import datetime
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

progress = {'n' : 0}

def print_to_stderr(*a):
	print(*a, file = sys.stderr)

def index_file(filename, args):
	f = open(filename, 'r')
	for line in f:
		p = line.find(" {\"")
		host = line[0:p]
		entry = json.loads(line[p+1:])
		for year, values in entry.items():
			progress['n'] = progress['n'] + 1
			values["_index"] = args.index
			if len(year)==4 and year.isdigit():
				if int(year) < 1991 or int(year) > 2021:
					continue
				values["date"]=year+'-01-01'
			elif len(year)==6:
				values["date"]=year[0:4]+'-'+year[4:6]+'-'+'01'
			values["host"]=host
			values["webarchive"]=args.webarchive
			tld_pos = host.rfind('.')
			if tld_pos>=0:
				values["tld"]=host[tld_pos+1:len(host)]
			values["m-last-update"] = datetime.now().isoformat()
			yield values

def dowork(args):
	client = Elasticsearch([args.server])
	successes = 0
	for f in args.file:
		for ok, action in streaming_bulk(
			client=client, actions=index_file(f, args)):
			successes += ok
	print("Bulk imported", successes, "of", progress['n'])
	client.close()

parser = ArgumentParser(description='Ingest CDX summary into elasticsearch')
parser.add_argument('-index', default='cdx-summary', help='name of the elasticsearch index pattern')
parser.add_argument('-server', default='localhost', help='server name of the elasticsearch server')
parser.add_argument('-webarchive', default="archive-org", help='name of webarchive where the data comes from')
parser.add_argument('file', nargs='*', help='summary file (can be several)')

args = parser.parse_args()
dowork(args)

