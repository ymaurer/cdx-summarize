#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import json

COLUMN_INDEX    = 0
COLUMN_FILENAME = 1
COLUMN_FILEPTR  = 2
COLUMN_KEY      = 3
COLUMN_LINE     = 4
COLUMN_YEAR     = 5


RES_COUNT    = 0
RES_N        = 1
RES_SIZE     = 2

def print_to_stderr(*a): 
    print(*a, file = sys.stderr)

def dowork(args):
    fd = []
    if args.noyear:
        nkey = 1
    else:
        nkey = 2
    all_eof = True
    i = 0
    for f in args.file:
        fp = open(f, 'r')
        l = fp.readline()
        if not l == '':
            all_eof = False
            splitline = l.split(args.sep)
            k = args.sep.join(splitline[0:nkey])
            if args.noyear:
                fd.append([i, f, fp, k, l])
            else:
                fd.append([i, f, fp, k, l, int(splitline[1])])
        i = i + 1
    # sort the files by their key
    fd.sort(key=lambda k:k[COLUMN_KEY])
    res = {}
    lastkey = ''
    while not all_eof:
        # first find out how many files have the same key on the current line
        nequal = 1
        keyfound = {fd[0][COLUMN_INDEX]:0}
        while nequal < len(fd) and fd[nequal][COLUMN_KEY] == fd[0][COLUMN_KEY]:
            keyfound[fd[nequal][COLUMN_INDEX]] = nequal
            nequal = nequal + 1
        # save the number of common lines for that file combination and their 2 last columns if needed
        skeyfound = sorted(keyfound.keys())
        reskey = '-'.join([str(x) for x in skeyfound])
        if not args.noyear:
            year = fd[0][COLUMN_YEAR]
        if not reskey in res:
            if args.noyear:
                res[reskey] = [0] * (1 + (2 * nequal if not args.nototal else 0))
            else:
                res[reskey] = {}
        if not args.noyear and not year in res[reskey]:
            res[reskey][year] = [0] * (1 + (2 * nequal if not args.nototal else 0))
        # if the key hasn't changed from the last line from the file(s), we don't need to increase the counter
        if not fd[0][COLUMN_KEY] == lastkey:
            if args.noyear:
                res[reskey][RES_COUNT] += 1
            else:
                res[reskey][year][RES_COUNT] += 1
        lastkey = fd[0][COLUMN_KEY]
        # keep adding the sums of the last two columns if wanted
        if not args.nototal:
            i = 0
            for k in skeyfound:
                tmpline = fd[keyfound[k]][COLUMN_LINE].split(args.sep)
                if args.noyear:
                    res[reskey][RES_N + 2 * i] += int(tmpline[-2])
                    res[reskey][RES_SIZE + 2 * i] += int(tmpline[-1])
                else:
                    res[reskey][year][RES_N + 2 * i] += int(tmpline[-2])
                    res[reskey][year][RES_SIZE + 2 * i] += int(tmpline[-1])
                i = i + 1
        # read the next line for those files who had the same key
        i = 0
        while i < nequal and i < len(fd):
            l = fd[i][COLUMN_FILEPTR].readline()
            if l == '':
                del fd[i]
            else:
                splitline = l.split(args.sep)
                k = args.sep.join(splitline[0:nkey])
                fd[i][COLUMN_KEY] = k
                fd[i][COLUMN_LINE] = l
                if not args.noyear:
                    fd[i][COLUMN_YEAR] = int(splitline[1])
                i = i + 1
        if len(fd) == 0:
            all_eof = True
        else:
            fd.sort(key=lambda k:k[COLUMN_KEY])
    if args.csv:
        if args.noyear:
            export_as_csv_simple(args, res)
        else:
            export_as_csv_with_years(args, res)
    else:
        jsonout = {}
        for k in res:
            jsonout[filename_from_key(args, k)] = res[k]
        print(json.dumps(jsonout))

def filename_from_key(args, k):
    filename = ''
    for e in k.split('-'):
        if len(filename):
            filename += ' AND '
        filename += args.file[int(e)]
    return filename

def print_csv_line(args, arr):
    s = '"'+args.outsep+'"'
    print('"'+s.join(arr)+'"')

def print_header_combi(args, res_sorted, out = []):
    for k in res_sorted:
        parts = k.split('-')
        name = filename_from_key(args, k)
        if len(parts) > 1:
            for e in parts:
                out.append(args.file[int(e)] + ' from (' + name + ')')
        else:
            out.append(args.file[int(parts[0])])
    print_csv_line(args, out)

def export_as_csv_simple(args, res):
    res_sorted = sorted(res)
    print('Count of hosts:')
    out = []
    for k in res_sorted:
        out.append(filename_from_key(args, k))
    print_csv_line(args, out)
    out = []
    for k in res_sorted:
        out.append(str(res[k][RES_COUNT]))
    print_csv_line(args, out)
    print('Count of URLs:')
    print_header_combi(args, res_sorted, [])
    out = []
    for k in res_sorted:
        parts = k.split('-')
        for i in range(0, len(parts)):
            out.append(str(res[k][RES_N + 2 * i]))
    print_csv_line(args, out)
    print('Size of compressed records:')
    print_header_combi(args, res_sorted, [])
    out = []
    for k in res_sorted:
        parts = k.split('-')
        for i in range(0, len(parts)):
            out.append(str(res[k][RES_SIZE + 2 * i]))
    print_csv_line(args, out)    

def export_as_csv_with_years(args, res):
    # find out which years exist
    years = {}
    for k in res:
        for y in res[k]:
            years[y] = True
    res_sorted = sorted(res)
    print('Hosts:')
    # print header
    out = ['Year']
    for k in res_sorted:
        out.append(filename_from_key(args, k))
    print_csv_line(args, out)
    # print the years
    for y in sorted(years):
        out = [str(y)]
        for k in res_sorted:
            if y in res[k]:
                out.append(str(res[k][y][RES_COUNT]))
            else:
                out.append('0')
        print_csv_line(args, out)
    print('Count of URLs:')
    print_header_combi(args, res_sorted, ['Year'])
    out = []
    for y in sorted(years):
        out = [str(y)]
        for k in res_sorted:
            parts = k.split('-')
            for i in range(0, len(parts)):
                if y in res[k]:
                    out.append(str(res[k][y][RES_N + 2 * i]))
                else:
                    out.append('0')
        print_csv_line(args, out)
    print('Size of compressed records:')
    print_header_combi(args, res_sorted, ['Year'])
    out = []
    for y in sorted(years):
        out = [str(y)]
        for k in res_sorted:
            parts = k.split('-')
            for i in range(0, len(parts)):
                if y in res[k]:
                    out.append(str(res[k][y][RES_SIZE + 2 * i]))
                else:
                    out.append('0')
        print_csv_line(args, out)


parser = ArgumentParser(description='Find the overlap between several sorted files and optionally sum last two columns')
parser.add_argument('-sep', default=' ', help='field separator (default is space)')
parser.add_argument('-outsep', default=',', help='output field separator (default is comma)')
parser.add_argument('-noyear', action="store_true", help='input file does not have a year column')
parser.add_argument('-nototal', action="store_true", help='do not sum the last two columns')
parser.add_argument('-csv', action="store_true", help='Export only CSV file')
parser.add_argument('file', nargs='*', help='file (can be several)')
args = parser.parse_args()
dowork(args)
