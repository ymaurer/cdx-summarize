#!/usr/bin/python3

# MIME summarizer module

import array

N_HTML      = 0
N_IMAGE     = 1
N_VIDEO     = 2
N_AUDIO     = 3
N_PDF       = 4
N_JS        = 5
N_JSON      = 6
N_FONT      = 7
N_CSS       = 8
N_OTHER     = 9
N_HTTP      = 10
N_HTTPS     = 11
N_TOTAL     = 12
S_FIRST     = 13
S_HTML      = S_FIRST
S_IMAGE     = S_FIRST + 1
S_VIDEO     = S_FIRST + 2
S_AUDIO     = S_FIRST + 3
S_PDF       = S_FIRST + 4
S_JS        = S_FIRST + 5
S_JSON      = S_FIRST + 6
S_FONT      = S_FIRST + 7
S_CSS       = S_FIRST + 8
S_OTHER     = S_FIRST + 9
S_HTTP      = S_FIRST + 10
S_HTTPS     = S_FIRST + 11
S_TOTAL     = S_FIRST + 12
TOTAL       = S_TOTAL + 1

def init_counter():
    return [0] * TOTAL 

def add_mime(a, mime, count = 1, size = 0):
    a[N_TOTAL] += count
    a[S_TOTAL] += size
    if mime == "text/html" or mime == "application/xhtml+xml" or mime == "text/plain":
        a[N_HTML] += count
        a[S_HTML] += size
    elif mime == "text/css":
        a[N_CSS] += count
        a[S_CSS] += size
    elif mime.find("image/") == 0:
        a[N_IMAGE] += count
        a[S_IMAGE] += size
    elif mime == "application/pdf":
        a[N_PDF] += count
        a[S_PDF] += size
    elif mime.find("video/") == 0:
        a[N_VIDEO] += count
        a[S_VIDEO] += size
    elif mime.find("audio/") == 0:
        a[N_AUDIO] += count
        a[S_AUDIO] += size
    elif mime == "application/javascript" or mime == "text/javascript" or  mime == "application/x-javascript":
        a[N_JS] += count
        a[S_JS] += size
    elif mime == "application/json" or mime == "text/json":
        a[N_JSON] += count
        a[S_JSON] += size
    elif mime.find("font/") == 0 or mime == "application/vnd.ms-fontobject" or mime.find("application/font") == 0 or mime.find("application/x-font") == 0:
        a[N_FONT] += count
        a[S_FONT] += size
    else:
        a[N_OTHER] += count
        a[S_OTHER] += size

def add_scheme(a, scheme, count = 1, size = 0):
    if scheme == 'http':
        a[N_HTTP] += count
        a[S_HTTP] += size
    elif scheme == 'https':
        a[N_HTTPS] += count
        a[S_HTTPS] += size

def as_dict(a):
    return {
        'n_html': a[N_HTML],
        'n_image': a[N_IMAGE],
        'n_video': a[N_VIDEO],
        'n_audio': a[N_AUDIO],
        'n_pdf': a[N_PDF],
        'n_js': a[N_JS],
        'n_json': a[N_JSON],
        'n_font': a[N_FONT],
        'n_css': a[N_CSS],
        'n_other': a[N_OTHER],
        'n_http': a[N_HTTP],
        'n_https': a[N_HTTPS],
        'n_total': a[N_TOTAL],
        's_html': a[S_HTML],
        's_image': a[S_IMAGE],
        's_video': a[S_VIDEO],
        's_audio': a[S_AUDIO],
        's_pdf': a[S_PDF],
        's_js': a[S_JS],
        's_json': a[S_JSON],
        's_font': a[S_FONT],
        's_css': a[S_CSS],
        's_other': a[S_OTHER],
        's_http': a[S_HTTP],
        's_https': a[S_HTTPS],
        's_total': a[S_TOTAL]
    }

def from_dict(d):
    a = init_counter()
    a[N_HTML] = d['n_html'] if 'n_html' in d else 0
    a[N_IMAGE] = d['n_image'] if 'n_image' in d else 0
    a[N_VIDEO] = d['n_video'] if 'n_video' in d else 0
    a[N_AUDIO] = d['n_audio'] if 'n_audio' in d else 0
    a[N_PDF] = d['n_pdf'] if 'n_pdf' in d else 0
    a[N_JS] = d['n_js'] if 'n_js' in d else 0
    a[N_JSON] = d['n_json'] if 'n_json' in d else 0
    a[N_FONT] = d['n_font'] if 'n_font' in d else 0
    a[N_CSS] = d['n_css'] if 'n_css' in d else 0
    a[N_OTHER] = d['n_other'] if 'n_other' in d else 0
    a[N_HTTP] = d['n_http'] if 'n_http' in d else 0
    a[N_HTTPS] = d['n_https'] if 'n_https' in d else 0
    a[N_TOTAL] = d['n_total'] if 'n_total' in d else 0
    a[S_HTML] = d['s_html'] if 's_html' in d else 0
    a[S_IMAGE] = d['s_image'] if 's_image' in d else 0
    a[S_VIDEO] = d['s_video'] if 's_video' in d else 0
    a[S_AUDIO] = d['s_audio'] if 's_audio' in d else 0
    a[S_PDF] = d['s_pdf'] if 's_pdf' in d else 0
    a[S_JS] = d['s_js'] if 's_js' in d else 0
    a[S_JSON] = d['s_json'] if 's_json' in d else 0
    a[S_FONT] = d['s_font'] if 's_font' in d else 0
    a[S_CSS] = d['s_css'] if 's_css' in d else 0
    a[S_OTHER] = d['s_other'] if 's_other' in d else 0
    a[S_HTTP] = d['s_http'] if 's_http' in d else 0
    a[S_HTTPS] = d['s_https'] if 's_https' in d else 0
    a[S_TOTAL] = d['s_total'] if 's_total' in d else 0
    return a