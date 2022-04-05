# Summarize CDX
The tools in this repo allow CDX file summarization to a more compact file format which can then be analyzed later on a workstation as opposed to a cluster. There are two file formats that the tools work with:
- .summary files with the format `host.tld {"year": {"n_XXX": A, ... "s_XXX":B}}` which hold information about 2nd level domains, years and some MIME type info. These are still quite large.
- files generated by `host_year_total.py` from the .summary and consumed by `overlap.py` discard all MIME type info and can also optionnally discard all info about years. These are very compact space-delimited text files.

The `host_year_total.py` can already answer some questions about the amount of data that has been archived by a given archive for a host, but do not hold any information on MIME types anymore.

# cdx-summarize

Use to create a summary for one or more CDX files per year with data about videos, images, html, pdf and http vs https sites. 
```
usage: cdx-summarize.py [-h] [--gz] [--nogz] [--monthly] [--compact] [--format {cdxj,cdx7,cdxNbams}] [file [file ...]]

Summarize CDX file(s) to JSONL, automatically uses gzip filter if file ends with .gz

positional arguments:
  file                  cdx file (can be several)

optional arguments:
  -h, --help            show this help message and exit
  --gz                  force use of gzip filter
  --nogz                force not using gzip filter
  --monthly             break up statistics into monthly buckets instead of yearly
  --compact             do not output fields that are 0
  --format {cdxj,cdx7,cdxNbams}
                        force use of cdx format (cdxNbams = N b a m s)
```

# combine-summary
This program combines several of these summaries into a single one where each 2nd level domain only appears once. It can also run on a single file where then any duplicate entries for a single 2nd level domain are added together.
```
usage: combine-summary.py [-h] [--yearly] [--compact] [file [file ...]]

Combine summary files generated by cdx-summary.py

positional arguments:
  file        summary file (can be several)

optional arguments:
  -h, --help  show this help message and exit
  --yearly    force output into yearly buckets
  --compact   do not output fields that are 0
```

# .summary Output file format
The output file format of `cdx-summarize` and `combine-summary` are files with the following structure:
```
host.tld {"year": {"n_XXX": A, ... "s_XXX":B}}
```
By default only the second-level domain is kept and all other host information is discarded so that information from all hosts in a second-level domain is aggregated together into a single entry. The years are determined by the date in the CDX(J) files. The `n_` fields are counters of the number of entries with a given MIME-type and the `s_` fields are the corresponding sizes of the compressed entries in the WARC files. Only entries with a HTTP status code of 2XX are counted, so redirects and errors etc. are ignored.

Example output (the newlines are for clarity):
```
bnl.lu {"2001":{"n_audio":0,"n_css":0,"n_font":0,"n_html":31,"n_http":31,"n_https":0,"n_image":0,"n_js":0,"n_json":0,"n_other":0,"n_pdf":0,"n_total":31,"n_video":0,"s_audio":0,"s_css":0,"s_font":0,"s_html":9323,"s_http":9323,"s_https":0,"s_image":0,"s_js":0,"s_json":0,"s_other":0,"s_pdf":0,"s_total":9323,"s_video":0},
"2002":{"n_audio":0,"n_css":0,"n_font":0,"n_html":175,"n_http":175,"n_https":0,"n_image":0,"n_js":0,"n_json":0,"n_other":0,"n_pdf":0,"n_total":175,"n_video":0,"s_audio":0,"s_css":0,"s_font":0,"s_html":52634,"s_http":52634,"s_https":0,"s_image":0,"s_js":0,"s_json":0,"s_other":0,"s_pdf":0,"s_total":52634,"s_video":0},
"2003":{"n_audio":0,"n_css":8,"n_font":0,"n_html":639,"n_http":728,"n_https":0,"n_image":44,"n_js":0,"n_json":0,"n_other":7,"n_pdf":30,"n_total":728,"n_video":0,"s_audio":0,"s_css":5268,"s_font":0,"s_html":1295481,"s_http":4680354,"s_https":0,"s_image":295235,"s_js":0,"s_json":0,"s_other":13156,"s_pdf":3071214,"s_total":4680354,"s_video":0}}
```

# host_year_total
It takes as an input a .summary file as described above and outputs a space-delimited file with only the total URLS and size per 2nd level domain and optionally also per year (by default on)
```
usage: host_year_total.py [-h] [-nototal] [-noyear] [file [file ...]]

extract a space-delimited file with the columns host [year] [n_total]
[s_total] webarchive from a summary file

positional arguments:
  file        summary file (can be several)

optional arguments:
  -h, --help  show this help message and exit
  -nototal    do not output the n_total and s_total columns
  -noyear     do not output the year column
```
Example output:
```
alvestedetocht.frl 2015 2 3750
alvestedetocht.frl 2016 108 483354679
alvestedetocht.frl 2018 34 2188664
amanjaya.frl 2018 4 1126074
amarins.frl 2018 2 1048
amateurfotograaf.frl 2018 9 77172
```
When the options `-nototal` and `-noyear` are used together, the output file will just consist of the hostnames present in the .summary file. The same result could be gotten faster and more easily using unix `cut` as in `cut -d' ' -f1 file.summary`.

# overlap
This programs computes some measures of overlap over files produced by host_year_total. The overlap is not in terms of individual URLs archived, but rather whether the different archives hold at least some files from the same 2nd level domain and also how many files each archive has and how much the compressed size is.
```
usage: overlap.py [-h] [-sep SEP] [-outsep OUTSEP] [-noyear] [-nototal] [-csv]
                  [file [file ...]]

Find the overlap between several sorted files and optionally sum last two
columns

positional arguments:
  file            file (can be several)

optional arguments:
  -h, --help      show this help message and exit
  -sep SEP        field separator (default is space)
  -outsep OUTSEP  output field separator (default is comma)
  -noyear         input file does not have a year column
  -nototal        do not sum the last two columns
  -csv            Export only CSV file
```
Example output:
```
# ./overlap.py ccfrl iafrl
{
    "iafrl": {
        "2018": [9914, 91825, 4977350765],
        "2015": [201, 9529, 414622814],
        "2019": [1180, 7556, 390007842],
        "2016": [305, 14103, 952210137],
        "2017": [231, 10954, 625164467],
        "2020": [89, 993, 25683591],
        "2013": [3, 9, 64115],
        "2014": [10, 470, 20817319]
    },
    "ccfrl": {
        "2017": [157, 3233, 33266613],
        "2020": [742, 66883, 1338230691],
        "2018": [89, 6006, 138654487],
        "2019": [469, 27020, 346900378],
        "2016": [45, 154, 582951],
        "2015": [6, 30, 140584]
    },
    "ccfrl AND iafrl": {
        "2017": [366, 44025, 799626968, 40128, 2033906308],
        "2018": [710, 153881, 2401927475, 73348, 2680314344],
        "2019": [620, 216463, 3596017472, 122342, 16451820932],
        "2016": [237, 2447, 12540308, 73238, 2448480091],
        "2020": [284, 115036, 1941213230, 34837, 3551740101],
        "2015": [40, 739, 5095146, 27836, 744771087],
        "2014": [9, 31, 162584, 447, 2293390]
    }
}
```
The first number in the array is the count of 2nd level domains that appear in the file. The second is the number of URLs and the third is the cumulative size of the compressed WARC records. For keys with more than one source archive (as in ccfrl AND iafrl in the example), the 2nd and 3rd column are for the first source archive, the 4th and 5th column are for the second source archive.
Alternatively the program can be run with the `-csv` switch and the output will be formatted as CSV for use in your favourite spreadsheet program. Example for a csv output:
```
Hosts:
"Year","ccfrl","ccfrl AND iafrl","iafrl"
"2013","0","0","3"
"2014","0","9","10"
"2015","6","40","201"
"2016","45","237","305"
"2017","157","366","231"
"2018","89","710","9914"
"2019","469","620","1180"
"2020","742","284","89"
Count of URLs:
"Year","ccfrl","ccfrl from (ccfrl AND iafrl)","iafrl from (ccfrl AND iafrl)","iafrl"
"2013","0","0","0","9"
"2014","0","31","447","470"
"2015","30","739","27836","9529"
"2016","154","2447","73238","14103"
"2017","3233","44025","40128","10954"
"2018","6006","153881","73348","91825"
"2019","27020","216463","122342","7556"
"2020","66883","115036","34837","993"
Size of compressed records:
"Year","ccfrl","ccfrl from (ccfrl AND iafrl)","iafrl from (ccfrl AND iafrl)","iafrl"
"2013","0","0","0","64115"
"2014","0","162584","2293390","20817319"
"2015","140584","5095146","744771087","414622814"
"2016","582951","12540308","2448480091","952210137"
"2017","33266613","799626968","2033906308","625164467"
"2018","138654487","2401927475","2680314344","4977350765"
"2019","346900378","3596017472","16451820932","390007842"
"2020","1338230691","1941213230","3551740101","25683591"
```
This works with more than 2 source archives but the output can become a bit unwieldy because a lot of columns need to be output if each combination exists. There is also an open question what it means if for the same 2nd level domain two different archives have a different of data. At this point we have reduced the information present in the input files so much that we cannot tell whether the archives have the same data or different one.

# Summarizing the MIME Types

## MIME Type short intro
There are hundreds of valid MIME Types registered with IANA (Internet Assigned Numbers Authority) and the current list can be viewed at [https://www.iana.org/assignments/media-types/media-types.xhtml](https://www.iana.org/assignments/media-types/media-types.xhtml). While this list is extensive, in reality webservers do not always conform to it and return other strings. Webbrowsers are quite leniant and do still handle the files correctly in most cases.

Also, web archives have different levels of information available about MIME types. There are the following:
1. MIME types as specified by the server
2. MIME types as determined by an external utility
For example the unix utility [file](https://linux.die.net/man/1/file) can be run with `file --mime-type` to determine some MIME types. [DROID](https://www.nationalarchives.gov.uk/documents/information-management/droid-user-guide.pdf) can be used to determine MIME types. It depends on each webarchive whether they do the characterisation of the files inside of the WARCs or not.

## Why summarize
The common MIME types are summarised in that they are grouped into several categories. This is mainly to enable the programs to run with less memory requirements (only the number of entries and sizes per category need to be kept). An added benefit is that then it becomes easier to compare the categories later.

## The categories used here:
The categories are specified in the module `mime_counter.py` as follows:
| MIME(s) | category | rationale |
| --- | --- | --- |
| text/html<br/>application/xhtml+xml<br/>text/plain | HTML | These are counted as "web-pages" by [Internet Archive](https://blog.archive.org/2016/10/23/defining-web-pages-web-sites-and-web-captures/) |
| text/css | CSS | interesting for changing usage in formatting pages |
| image/* | IMAGE | all image types are grouped together |
| application/pdf | PDF | Interesting independetly, although IA groups PDFs in "web-page" too |
| video/* | VIDEO | all videos |
| audio/* | AUDIO | all audio types |
| application/javascript<br/>text/javascript<br/>application/x-javascript | JS | these 3 MIME types are common for javascript |
| application/json<br/>text/json | JSON | relatively common and indicates dynamic pages |
| font/*<br/>application/vnd.ms-fontobject<br/>application/font*<br/>application/x-font* | FONT | Usage of custom fonts |

# Data sources used

## Internet Archive metadata summary service
It's possible to get metadata in JSON format from the Internet Archive using this service:

[https://web.archive.org/__wb/search/metadata?q=tld:lu](https://web.archive.org/__wb/search/metadata?q=tld:lu)

Here with the example of the Top-level Domain (TLD) ".lu". There is unfortunately not that much public information available on how exactly these numbers were calculated. The following information is available in the JSON result:
- "captures", per year, per MIME-type, probably the number of resources with status 2XX that were captured
- "new", probably the new domains and hosts captured in the year the metadata was computed
- "new_urls", per year, per MIME-type, probably the number of *new* resources with status 2XX that were captured (according to their SURT notation)
- "timestamp", probably when the summary was last calculated
- "total", per year, probably the total number of 2nd level domains and hosts that returned resources with a 2XX status. 
- "type", the query type, in this case always *tld*
- "urls", per year, per MIME-type, probably the number of resources with status 2XX that were captured and that were unique during that year, according to their SURT notation
- "urls_total_compressed_size", per year, per MIME-type, the size of the compressed WARC records for "urls"

As you can see, there are some unknowns in the data and especially the "total" key seems to be strange, since for the TLD .lu it reports 2285 domains only when the CDX files show otherwise. At the date of writing the `timestamp` is the 22nd of September 2020, so the data for at least 2020 is incomplete.

## CDX files
Using Ilya Kreymer's excellent [cdx-index-client](https://github.com/ikreymer/cdx-index-client), you can download the CDX files from any CDX server that you have access to. 

### Internet Archive CDX server
Using cdx-index-client, you can download the data from the Internet Archive's CDX server which lives at:
(http://web.archive.org/cdx/search/cdx)[http://web.archive.org/cdx/search/cdx]
There is a good description of the capabilities on (Karl-Rainer Blumthal's archive-it blogpost)[https://support.archive-it.org/hc/en-us/articles/115001790023-Access-Archive-It-s-Wayback-index-with-the-CDX-C-API]

### Common-crawl CDX files
Again, using cdx-index-client, you can download the CDXJ indexes from the common-crawl.

### Luxembourg Webarchive CDXJ files
Since I have access to the CDXJ files of the Luxembourg Webarchive, I could run the commands locally.

## Limitations
Some CDXJ files from the commoncrawl do not have MIME types. These are only counted in the `_other` fields. Some dates are also invalid, these lines are ignored.

# Ingesting into elasticsearch
One way of examiming the summary is to ingest them into elasticsearch and then run analytics on them using Kibana.
