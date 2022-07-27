#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import gzip
import json
import urllib
import mime_counter

# CDX(J) formats supported
FORMAT_UNKNOWN = 0
FORMAT_CDX7 = 1
FORMAT_CDXJ = 2
FORMAT_CDXNbams = 3
# Used to filter out invalid dates
MIN_YEAR = 1991
MAX_YEAR = 2022
# Used to indicate End of String
INT_MAX = 2147483647

# Dictionary to hold the data per 2nd-level domain, per year
Hosts = {}

def print_to_stderr(*a): 
	print(*a, file = sys.stderr)

# the surt holds the inverted domain name as a sequence delimited by comma
# so all we need to do is to go to the end of the domain or the second comma
# and invert the parts
def host_from_surt(surt, only2 = False):
	p = surt.find(',')
	if p == -1:
		return ''
	p2 = surt.find(')', p + 1)
	if p2 == -1:
		return ''
	parts = surt[0:p2].split(',')
	if only2:
		if len(parts) > 1:
			return parts[1] + '.' + parts[0]
		else:
			return parts[0]
	else:
		parts.reverse()
		return '.'.join(parts)


def lvl2_from_surt(surt):
	return host_from_surt(surt, True)

# the massaged URL has no protocol for http and https and strips the 'www'
# so we look for the first non-host character and if there is no dot in the host
# we reject it since it will not be a correct hostname
def host_from_massagedURL(url):
	p1 = url.find('/')
	p2 = url.find(':')
	p3 = url.find('?')
	if p1 == -1:
		p1 = INT_MAX
	if p2 == -1:
		p2 = INT_MAX
	if p3 == -1:
		p3 = INT_MAX
	p = min(p1, p2, p3, len(url))
	return url[0:p]

def lvl2_from_massagedURL(url):
	hostparts = host_from_massagedURL(url).split('.')
	if len(hostparts) < 2:
		return ''
	else:
		return hostparts[len(hostparts)-2]+'.'+hostparts[len(hostparts)-1]
	
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
def parse_line_cdxj(line, ismonthly, fullhost=False):
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
		if fullhost:
			summarize_line(host_from_surt(tokens[0]), year, info)
		else:
			summarize_line(lvl2_from_surt(tokens[0]), year, info)
	except Exception as inst:
		print_to_stderr('cdxj: could not parse line', inst)

# parse CDX7 file as returned by Internet Archive's CDX server by default
def parse_line_cdx7(line, ismonthly, fullhost=False):
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
		if fullhost:
			summarize_line(host_from_surt(tokens[0]), year, info)
		else:
			summarize_line(lvl2_from_surt(tokens[0]), year, info)
	except Exception as inst:
		print_to_stderr('cdx: could not parse line', inst)

def parse_line_cdxNbams(line, ismonthly, fullhost=False):
	tokens = line.split()
	if len(tokens) < 5:
		return
	year = year_from_date(tokens[1], ismonthly)
	if year == -1:
		return
	info = {"url": tokens[2], "mime": tokens[3],"status":tokens[4],"length":0}
	try:
		if fullhost:
			summarize_line(host_from_massagedURL(tokens[0]), year, info)
		else:
			summarize_line(lvl2_from_massagedURL(tokens[0]), year, info)
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

def outputResults(args):
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

def determine_cdx_type(line):
	tokens = line.split()
	if len(tokens) < 3:
		return FORMAT_UNKNOWN
	if len(tokens)>=6:
		if tokens[0]=='CDX':
			if line[0:14] == ' CDX N b a m s':
				return FORMAT_CDXNbams
			else:
				return FORMAT_UNKNOWN

	# all supported formats have the date as a 14 digit string in the second place
	if (len(tokens[1]) != 14):
		return FORMAT_UNKNOWN
	# check if the line ends with a "} indicative of JSON
	if line.rstrip()[-2:] == '"}':
		return FORMAT_CDXJ
	if len(tokens)==7:
		return FORMAT_CDX7
	elif len(tokens)==10:
		return FORMAT_CDXNbams
	return FORMAT_UNKNOWN

def cdx_type_from_args(args):
	if args.format=='cdxj':
		return FORMAT_CDXJ
	elif args.format=='cdx7':
		return FORMAT_CDX7
	elif args.format=='cdxNbams':
		return FORMAT_CDXNbams
	else:
		return FORMAT_UNKNOWN

def read_cdx_file(args, fil):
	line = fil.readline()
	ftype = cdx_type_from_args(args)
	if ftype == FORMAT_UNKNOWN:
		ftype = determine_cdx_type(line)
	if ftype == FORMAT_CDXJ:
		parse_line_cdxj(line.rstrip(), args.monthly, args.fullhost)
		for line in fil:
			try:
				parse_line_cdxj(line.rstrip(), args.monthly, args.fullhost)
			except Exception as inst:
				print_to_stderr("Unexpected error:", inst, line)
	elif ftype == FORMAT_CDX7:
		parse_line_cdx7(line.rstrip(), args.monthly, args.fullhost)
		for line in fil:
			try:
				parse_line_cdx7(line.rstrip(), args.monthly, args.fullhost)
			except Exception as inst:
				print_to_stderr("Unexpected error:", inst, line)
	elif ftype == FORMAT_CDXNbams:
		parse_line_cdxNbams(line.rstrip(), args.monthly, args.fullhost)
		for line in fil:
			try:
				parse_line_cdxNbams(line.rstrip(), args.monthly, args.fullhost)
			except Exception as inst:
				print_to_stderr("Unexpected error:", inst, line)					
	else:
		print_to_stderr("Unsupported cdx format: ", f, line)

def dowork(args):
	for f in args.file:
		if (args.gz or (len(f) > 3 and f[-3:] == '.gz')) and (not args.nogz):
			try:
				with gzip.open(f, mode='rt', encoding=args.encoding) as z:
					read_cdx_file(args, z)
			except Exception as inst:
				print_to_stderr("Error", inst, f)
		else:
			try:
				with open(f, 'r', encoding=args.encoding) as fil:
					read_cdx_file(args, fil)
			except Exception as inst:
				print_to_stderr("Error", inst, f)
	outputResults(args)


parser = ArgumentParser(description='Summarize CDX file(s) to JSONL, automatically uses gzip filter if file ends with .gz')
parser.add_argument('--gz', action="store_true", help='force use of gzip filter')
parser.add_argument('--nogz', action="store_true", help='force not using gzip filter')
parser.add_argument('--monthly', action="store_true", help='break up statistics into monthly buckets instead of yearly')
parser.add_argument('--compact', action="store_true", help='do not output fields that are 0')
parser.add_argument('--fullhost', action="store_true", default=False, help='aggregate by full hostname instead of second level domain')
parser.add_argument('--format',choices=['cdxj','cdx7','cdxNbams'], help='force use of cdx format (cdxNbams = N b a m s)')
parser.add_argument('--encoding', action="store", default='utf-8', help='encoding, e.g. iso-8859-1 (default is your locale\'s defaut encoding, probably utf-8 on Linux). All CDX files have to have the same encoding')
parser.add_argument('file', nargs='*', help='cdx file (can be several)')

args = parser.parse_args()
dowork(args)
