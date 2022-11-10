#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import gzip
import json
import urllib
import mime_counter
import re
import CdxParser

# Used to filter out invalid dates
MIN_YEAR = 1991
MAX_YEAR = 2022

# Dictionary to hold the data per domain, per year (or yearmonth)
Hosts = {}

def print_to_stderr(*a): 
	print(*a, file = sys.stderr)

def summarize_line(info):
	if not 'agg' in info:
		return
	agg = info['agg']
	if not agg in Hosts:
		Hosts[agg] = {}
	date = info['date']
	if not date in Hosts[agg]:
		Hosts[agg][date] = mime_counter.init_counter()
	if not 'mime' in info:
		info['mime']='unknown'
	mime_counter.add_mime(Hosts[agg][date], info["mime"], 1, info["length"])
	mime_counter.add_scheme(Hosts[agg][date], info['scheme'], 1, info["length"])

def output_results(args):
	dict_items = Hosts.items()
	sorted_items = sorted(dict_items)
	for lvl2, value in sorted_items:
		out = {}
		for year in value:
			if args.compact:
				tmp = mime_counter.as_dict(value[year])
				out[year] = {}
				for k in tmp:
					if tmp[k] > 0:
						out[year][k] = tmp[k]
			else:
				out[year] = mime_counter.as_dict(value[year])
		print(lvl2, json.dumps(out))

# output only the values for the key agg_by (aggregate_by) and then delete that key from the dictionary
def output_partial_results(args, agg_by):
	if agg_by in Hosts:
		out = {}
		for year in Hosts[agg_by]:
			if args.compact:
				tmp = mime_counter.as_dict(Hosts[agg_by][year])
				out[year] = {}
				for k in tmp:
					if tmp[k] > 0:
						out[year][k] = tmp[k]
			else:
				out[year] = mime_counter.as_dict(Hosts[agg_by][year])
		print(agg_by, json.dumps(out))
		del Hosts[agg_by]

def determine_cdx_type(line):
	tokens = line.split()
	if len(tokens) < 3:
		return CdxParser.FORMAT_UNKNOWN
	if len(tokens)>=6:
		if line.strip() == 'CDX N b a m s k r M S V g':
			return CdxParser.FORMAT_CDXNbamskrMSVg
		if tokens[0]=='CDX':
			if line[0:14] == ' CDX N b a m s':
				return CdxParser.FORMAT_CDXNbams
			else:
				return CdxParser.FORMAT_UNKNOWN
	# all supported formats have the date as a 14 digit string in the second place
	if (len(tokens[1]) != 14):
		return CdxParser.FORMAT_UNKNOWN
	# check if the line ends with a "} indicative of JSON
	if line.rstrip()[-2:] == '"}':
		return CdxParser.FORMAT_CDXJ
	if len(tokens)==7:
		return CdxParser.FORMAT_CDX7
	elif len(tokens)==10:
		return CdxParser.FORMAT_CDXNbams
	return CdxParser.FORMAT_UNKNOWN

def cdx_type_from_args(args):
	if args.format=='cdxj':
		return CdxParser.FORMAT_CDXJ
	elif args.format=='cdx7':
		return CdxParser.FORMAT_CDX7
	elif args.format=='cdxNbams':
		return CdxParser.FORMAT_CDXNbams
	elif args.format=='cdxNbamskrMSVg':
		return CdxParser.FORMAT_CDXNbamskrMSVg
	else:
		return CdxParser.FORMAT_UNKNOWN

def read_cdx_file(args, fil, filename):
	line = fil.readline()
	ftype = cdx_type_from_args(args)
	if ftype == CdxParser.FORMAT_UNKNOWN:
		ftype = determine_cdx_type(line)
	if ftype == CdxParser.FORMAT_UNKNOWN:
		print_to_stderr("Unsupported cdx format: ", filename, line)
		return
	parser = CdxParser.CdxParser(ftype, args.monthly, args.fullhost)
	aggregate_by = ''
	res = parser.parse_line(line)
	if 'agg' in res:
		aggregate_by = res['agg']
		summarize_line(res)
	for line in fil:
		try:
			res = parser.parse_line(line)
			summarize_line(res)
			if args.assume_unique:
				if 'agg' in res and res['agg'] != aggregate_by:
					output_partial_results(args, aggregate_by)
					aggregate_by = res['agg']
		except Exception as inst:
			print_to_stderr("Unexpected error:", filename, inst, line)

def dowork(args):
	for f in args.file:
		if (args.gz or (len(f) > 3 and f[-3:] == '.gz')) and (not args.nogz):
			try:
				with gzip.open(f, mode='rt', encoding=args.encoding) as z:
					read_cdx_file(args, z, f)
			except Exception as inst:
				print_to_stderr("Error", inst, f)
		else:
			try:
				with open(f, 'r', encoding=args.encoding) as fil:
					read_cdx_file(args, fil, f)
			except Exception as inst:
				print_to_stderr("Error (dowork)", inst, f)
	output_results(args)


if __name__ == '__main__':
	parser = ArgumentParser(description='Summarize CDX file(s) to JSONL, automatically uses gzip filter if file ends with .gz')
	parser.add_argument('--gz', action="store_true", help='force use of gzip filter')
	parser.add_argument('--nogz', action="store_true", help='force not using gzip filter')
	parser.add_argument('--monthly', action="store_true", help='break up statistics into monthly buckets instead of yearly')
	parser.add_argument('--compact', action="store_true", help='do not output fields that are 0')
	parser.add_argument('--fullhost', action="store_true", default=False, help='aggregate by full hostname instead of second level domain')
	parser.add_argument('--assume_unique', action="store_true", default=False, help='assume aggregation entry only appears in a continous run in the CDX file(s) (OK for single, sorted CDX with --fullhost)')
	parser.add_argument('--format',choices=['cdxj','cdx7','cdxNbams', 'cdxNbamskrMSVg'], help='force use of cdx format (cdxNbams = N b a m s)')
	parser.add_argument('--encoding', action="store", default='utf-8', help='encoding, e.g. iso-8859-1 (default is your locale\'s defaut encoding, probably utf-8 on Linux). All CDX files have to have the same encoding')
	parser.add_argument('file', nargs='*', help='cdx file (can be several)')
	args = parser.parse_args()
	dowork(args)
