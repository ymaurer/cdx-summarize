import re
import json

# CDX(J) formats supported
FORMAT_UNKNOWN = 0
FORMAT_CDX7 = 1
FORMAT_CDXJ = 2
FORMAT_CDXNbams = 3
FORMAT_CDXNbamskrMSVg = 4

class CdxParser:
    # ----- Regular expressions for the CDX formats
    # CDX N b a m s k r M S V g
    # CDX format from openwayback with also the compressed size information
    # N massaged url        surt
    # b date                year + month
    # a original url        scheme
    # m mime type           mime
    # s response code       status
    # k checksum            unused
    # r redirect            unused
    # M meta tags           unused
    # S comp. record size   size
    # V file offset         unused
    # g file name           unused
    # surt: TLD,2D[,3D,4D])[/]
    # \s+(?P<year>[0-9][0-9][0-9][0-9])(?P<month>[0-9][0-9])\d+\s+
    reExprCDXNbamskrMSVg = r'^(?P<surt>([^ ):,]+)(,[^ ):,]+)*)(?:[):]\S*\s+|\s+)(?P<year>[0-9][0-9][0-9][0-9])(?P<month>[0-9][0-9])\d+\s+(?:(?P<scheme>https?)://)?\S+\s+(?P<mime>\S+)\s+(?P<status>\S+)\s+\S+\s+\S+\s+\S+\s+(?P<length>\S+)'

    # CDX N b a m s (the N is not in surt format)
    # CDX format used by openwayback historically. Additionnal fields are ignored
    # N massaged URL        host
    # b date                year + month
    # a original url        scheme
    # m mime type           mime
    # s response code       status
    reExprCDXNbams = r'^(?P<host>[^ /:]+)\S*\s+(?P<year>[0-9][0-9][0-9][0-9])(?P<month>[0-9][0-9])\d+\s+(?:(?P<scheme>https?)://)?\S+\s+(?P<mime>\S+)\s+(?P<status>\S+)'

    # CDX N b a m s k S
    # CDX7 format returned by Internet Archive's CDX server 
    # N massaged url        surt
    # b date                year + month
    # a original url        scheme
    # m mime type           mime
    # s response code       status
    # k checksum            unused
    # S comp. record size   size
    reExprCDX7 = r'^(?P<surt>([^ ):,]+)(,[^ ):,]+)*)(?:[):]\S*\s+|\s+)(?P<year>[0-9][0-9][0-9][0-9])(?P<month>[0-9][0-9])\d+\s+(?:(?P<scheme>https?)://)?\S+\s+(?P<mime>\S+)\s+(?P<status>\S+)\s+\S+\s+(?P<length>\S+)'

    # CDXJ
    # format used by pywb and returned by the common crawl
    # N massaged url        surt
    # b date                year + month
    # JSON					data
    reExprCDXJ = r'^(?P<surt>([^ ):,]+)(,[^ ):,]+)*)(?:[):]\S*\s+|\s+)(?P<year>[0-9][0-9][0-9][0-9])(?P<month>[0-9][0-9])\d+\s+(?P<data>.*$)'

    def __init__(self, format, monthly=False, fullhost=False):
        self.monthly = monthly
        self.fullhost = fullhost
        self.only200 = True
        if format == FORMAT_CDX7:
            self.re_line = re.compile(self.reExprCDX7)
            self.has_json = False
            self.surt = True
        elif format == FORMAT_CDXJ:
            self.re_line = re.compile(self.reExprCDXJ)
            self.has_json = True
            self.surt = True
        elif format == FORMAT_CDXNbams:
            self.re_line = re.compile(self.reExprCDXNbams)
            self.has_json = False
            self.surt = False
        elif format == FORMAT_CDXNbamskrMSVg:
            self.re_line = re.compile(self.reExprCDXNbamskrMSVg)
            self.has_json = False
            self.surt = True

    def agg_from_surt(self, surt):
        parts = surt.split(',')
        if self.fullhost:
            parts.reverse()
            return '.'.join(parts)
        else:
            if len(parts) > 1:
                return parts[1] + '.' + parts[0]
            else:
                return ''
    
    def lvl2_from_host(self, host):
        p = host.rfind('.')
        if p > -1:
            p1 = host.rfind('.', 0, p -1)
            return host[p1+1:]
        return host

    def parse_line(self, line):
        m = self.re_line.match(line)
        if m:
            vars = m.groupdict()
            if self.only200 and 'status' in vars and vars['status'][0:1] != '2':
                return {}
            ret = {}
            # some CDX files might have metadata records, do not count those
            if 'mime' in vars and vars['mime']=='application/warc-fields':
                return {}
            # the date can be just YYYY or YYYYMM
            if self.monthly:
                retdate = int(vars['year'] + vars['month'])
            else:
                retdate = int(vars['year'])
            # Aggregation key is either the second level domain or the full host
            if self.surt:
                retagg = self.agg_from_surt(vars['surt'])
            else:
                if self.fullhost:
                    retagg = vars['host']
                else:
                    retagg = self.lvl2_from_host(vars['host'])
            # line has embedded JSON
            if self.has_json:
                d = json.loads(vars['data'])
                if self.only200 and 'status' in d and d['status'][0:1] != '2':
                    return {}
                # some CDXJ files have metadata records, do not count those
                if 'mime' in d and d['mime']=='application/warc-fields':
                    return {}
                retsize = 0
                if 'length' in d and d['length'].isnumeric():
                    retsize = int(d['length'])
                retscheme = ''
                if 'url' in d and len(d['url']) >= 8:
                    if d['url'][0:7] == 'http://':
                        retscheme = 'http'
                    elif d['url'][0:8] == 'https://':
                        retscheme = 'https'
                retmime = 'unknown'
                if 'mime' in d:
                    retmime = d['mime']
                return {'date' : retdate, 'agg' : retagg, 'scheme': retscheme, 'mime': retmime, 'length' : retsize}
            else:
                # line comes fully from the regex
                retsize = 0
                if 'length' in vars and vars['length'].isnumeric():
                    retsize = int(vars['length'])
                return {'date' : retdate, 'agg' : retagg, 'scheme': vars['scheme'], 'mime': vars['mime'], 'length' : retsize}
        return {}
