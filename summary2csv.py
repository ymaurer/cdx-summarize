#!/usr/bin/python3

from argparse import ArgumentParser
import sys
import json
import mime_counter

def print_to_stderr(*a):
	print(*a, file = sys.stderr)
	
def print_csv_line(args, arr):
	if args.quoted:
		s = '"'+args.outsep+'"'
		print('"'+s.join(arr)+'"')
	else:
		print(args.outsep.join(arr))

def print_header(args):
	fields = mime_counter.as_dict(mime_counter.init_counter())
	out = ['domainname', 'year']
	for f, v in sorted(fields.items()):
		out.append(str(f))
	print_csv_line(args, out)

def addFile(args, filename):
	f = open(filename, 'r', errors="ignore")
	keys = sorted(mime_counter.as_dict(mime_counter.init_counter()).keys())
	for line in f:
		p = line.find(" {\"")
		host = line[0:p]
		entry = json.loads(line[p+1:])
		for year, values in sorted(entry.items()):
			out = [host, str(year)]
			nonzero = False
			for k in keys:
				if k in values:
					out.append(str(values[k]))
					if values[k] != 0:
						nonzero = True
				else:
					out.append('0')
			if nonzero:
				print_csv_line(args, out)

def dowork(args):
	if not args.noheader:
		print_header(args)
	for f in args.file:
		try:
			addFile(args, f)
		except Exception as inst:
			print_to_stderr("Error", inst, f)

parser = ArgumentParser(description='transform a summary file to a space-delimited file with host year and all the other columns')
parser.add_argument('-outsep', default=' ', help='output field separator (default is space)')
parser.add_argument('-noheader', action="store_true", help='No header in CSV file')
parser.add_argument('-quoted', default=False, action="store_true", help='enclose field values in double-quotes (")')
parser.add_argument('file', nargs='*', help='summary file (can be several)')

args = parser.parse_args()
dowork(args)
