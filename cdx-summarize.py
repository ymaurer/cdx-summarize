#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import gzip
import json
import urllib
from urllib.parse import urlparse
import mime_counter

# CDX(J) formats supported
FORMAT_UNKNOWN = 0
FORMAT_CDX7 = 1
FORMAT_CDXJ = 2
# Used to filter out invalid dates
MIN_YEAR = 1991
MAX_YEAR = 2021

# Dictionary to hold the data per 2nd-level domain, per year
Hosts = {}

def print_to_stderr(*a): 
	print(*a, file = sys.stderr)

def lvl2_from_surt(surt):
	p = surt.find(',')
	if p == -1:
		return '';
	p1 = surt.find(',', p + 1)
	p2 = surt.find(')', p + 1)
	if p1 == -1:
		if p2 == -1:
			return ''
		else:
			return surt[p + 1:p2]+'.'+surt[0:p]
	else:
		if p2 == -1:
			return surt[p + 1:p1]+'.'+surt[0:p]
		elif p1 < p2:
			return surt[p + 1:p1]+'.'+surt[0:p]
		else:
			return surt[p + 1:p2]+'.'+surt[0:p]

def year_from_date(date, ismonthly):
	if len(date) < 6:
		return -1
	if ismonthly:
		year = date[0:6]
	else:
		year = date[0:4]
	if year.isdigit():
		if ismonthly:
			return int(year)
		else:
			yi = int(year)
			if yi >= MIN_YEAR and yi <= MAX_YEAR:
				return yi
	return -1

def scheme_from_url(url):
	if len(url)<8:
		return ''
	if url[0:7] == 'http://':
		return 'http'
	elif url[0:8] == 'https://':
		return 'https'
	return ''

# parse CDXJ file
def parse_line_cdxj(line, ismonthly):
	tokens = line.split()
	if len(tokens) < 3:
		return
	year = year_from_date(tokens[1], ismonthly)
	if year == -1:
		return
	p = line.find(" {\"") + 1
	p1 = line.rfind("\"}")
	if p == -1:
		return
	try:
		info = json.loads(line[p:p1+2])
		summarize_line(lvl2_from_surt(tokens[0]), year, info)
	except Exception as inst:
		print_to_stderr('cdxj: could not parse line', inst)

# parse CDX7 file as returned by Internet Archive's CDX server by default
def parse_line_cdx7(line, ismonthly):
	tokens = line.split()
	if len(tokens) < 7:
		return
	year = year_from_date(tokens[1], ismonthly)
	if year == -1:
		return
	if tokens[6] == '-':
		tokens[6] = '0'
	info = {"url": tokens[2], "mime": tokens[3],"status":tokens[4],"hash":tokens[5],"length":tokens[6]}
	try:
		summarize_line(lvl2_from_surt(tokens[0]), year, info)
	except Exception as inst:
		print_to_stderr('cdx: could not parse line', inst)

def summarize_line(lvl2, year, info):
	if len(lvl2) < 1:
		return
	if "status" in info and info["status"][0:1] == "2":
		scheme = scheme_from_url(info['url'])
		if not lvl2 in Hosts:
			Hosts[lvl2] = {}
		if not year in Hosts[lvl2]:
			Hosts[lvl2][year] = mime_counter.init_counter()
		if not 'mime' in info:
			info['mime']='unknown'
		mime_counter.add_mime(Hosts[lvl2][year], info["mime"], 1, int(info["length"]))
		mime_counter.add_scheme(Hosts[lvl2][year], scheme, 1, int(info["length"]))

def outputResults():
	dict_items = Hosts.items()
	sorted_items = sorted(dict_items)
	for lvl2, value in sorted_items:
		out = {}
		for year in value:
			out[year] = mime_counter.as_dict(value[year])
		print(lvl2, json.dumps(out))

def determine_cdx_type(line):
	tokens = line.split()
	if len(tokens) < 3:
		return FORMAT_UNKNOWN
	# all supported formats have the date as a 14 digit string in the second place
	if (len(tokens[1]) != 14):
		return FORMAT_UNKNOWN
	# check if the line ends with a "} indicative of JSON
	if line.rstrip()[-2:] == '"}':
		return FORMAT_CDXJ
	if len(tokens) < 7:
		return FORMAT_UNKNOWN
	return FORMAT_CDX7

def dowork(args):
	for f in args.file:
		if (args.gz or (len(f) > 3 and f[-3:] == '.gz')) and (not args.nogz):
			try:
				with gzip.open(f, mode='rt') as z:
					line = z.readline()
					ftype = determine_cdx_type(line)
					if ftype == FORMAT_CDXJ:
						parse_line_cdxj(line.rstrip(), args.monthly)
						for line in z:
							try:
								parse_line_cdxj(line.rstrip(), args.monthly)
							except Exception as inst:
								print_to_stderr("Unexpected error:", inst, line)
					elif ftype == FORMAT_CDX7:
						parse_line_cdx7(line.rstrip(), args.monthly)
						for line in z:
							try:
								parse_line_cdx7(line.rstrip(), args.monthly)
							except Exception as inst:
								print_to_stderr("Unexpected error:", inst, line)
					else:
                                            print_to_stderr("Unsupported cdx format: ", f, line)
			except Exception as inst:
				print_to_stderr("Error", inst, f)
		else:
			fil = open(f, 'r')
			line = fil.readline()
			ftype = determine_cdx_type(line)
			if ftype == FORMAT_CDXJ:
				parse_line_cdxj(line.rstrip(), args.monthly)
				for line in fil:
					try:
						parse_line_cdxj(line.rstrip(), args.monthly)
					except Exception as inst:
						print_to_stderr("Unexpected error:", inst, line)
			elif ftype == FORMAT_CDX7:
				parse_line_cdx7(line.rstrip(), args.monthly)
				for line in fil:
					try:
						parse_line_cdx7(line.rstrip(), args.monthly)
					except Exception as inst:
						print_to_stderr("Unexpected error:", inst, line)
			else:
				print_to_stderr("Unsupported cdx format: ", f, line)
	outputResults()


parser = ArgumentParser(description='Summarize CDX file(s) to JSONL, automatically uses gzip filter if file ends with .gz')
parser.add_argument('--gz', action="store_true", help='force use of gzip filter')
parser.add_argument('--nogz', action="store_true", help='force not using gzip filter')
parser.add_argument('--monthly', action="store_true", help='break up statistics into monthly buckets instead of yearly')
parser.add_argument('file', nargs='*', help='cdx file (can be several)')

args = parser.parse_args()
dowork(args)
