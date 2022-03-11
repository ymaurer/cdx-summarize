#!/usr/bin/python3

from argparse import ArgumentParser
import sys
import json
import mime_counter

def print_to_stderr(*a):
	print(*a, file = sys.stderr)

def addFile(args, filename):
	f = open(filename, 'r', errors="ignore")
	for line in f:
		p = line.find(" {\"")
		host = line[0:p]
		entry = json.loads(line[p+1:])
		if args.nototal and args.noyear:
			print(host)
		elif args.nototal:
			for year in sorted(entry):
				print(host,year)
		else:
			for year, values in sorted(entry.items()):
				if 'n_total' in values and values['n_total'] > 0:
					if 's_total' in values:
						print(host,year,values['n_total'],values['s_total'])
					else:
						print(host,year,values['n_total'],0)

def dowork(args):
	for f in args.file:
		try:
			addFile(args, f)
		except Exception as inst:
			print_to_stderr("Error", inst, f)

parser = ArgumentParser(description='extract a space-delimited file with the columns host [year] [n_total] [s_total] webarchive from a summary file')
parser.add_argument('-nototal', action="store_true", help='do not output the n_total and s_total columns')
parser.add_argument('-noyear', action="store_true", help='do not output the year column')
parser.add_argument('file', nargs='*', help='summary file (can be several)')

args = parser.parse_args()
dowork(args)
