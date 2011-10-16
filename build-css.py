import sys, os, cssmin, optparse, urllib, json, re
from termcolor import colored
from datetime import date
from pprint import pprint

# initial options
base_dir            =   os.path.join(os.getcwd(), 'css')
current_version     =   json.load(urllib.urlopen('https://github.com/api/v2/json/repos/show/dryan/css-smart-grid/tags'))['tags'].keys().pop()
gutter_width        =   20
columns             =   12
ie_fallback_class   =   "oldie"
ie_fallback_width   =   960

parser  =   optparse.OptionParser()
parser.add_option('--version', '-v', default = False, help = "The version to tag the files with. Defaults to the current latest tag from Github. Pass +1 to increment by 1 minor version.")
parser.add_option('--stdout', '-o', dest = "stdout", action="store_true", default = False, help = "Print to stdout.")
parser.add_option('--gutter-width', '-g', default = gutter_width, help = "The width of the gutters between each column.")
parser.add_option('--columns', '-c', default = columns, help = "The number of columns to create")
parser.add_option('--ie-fallback-class', default = ie_fallback_class, help = "The class name to use for IE fallback support. Defaults to 'oldie'.")
parser.add_option('--ie-fallback-width', default = ie_fallback_width, help = "The breakpoint to use for IE fallback support. Must be one of 320, 480, 768, 960, 1200 or 1920. Defaults to 960.")
parser.add_option('--debug', dest = "debug", action = "store_true", default = False, help = "Print debugging messages to stdout.")
opts, args   =   parser.parse_args()

if not opts.version and len(args):
    opts.version    =   args[0]

if opts.version and opts.version == '+1':
    cv              =   current_version.split('.')
    minor_number    =   int(cv.pop()) + 1
    cv.append(u'%d' % minor_number)
    current_version =   ".".join(cv)
    opts.version    =   current_version
    
if not opts.version:
    opts.version    =   current_version
    
if not re.search(r"^[\d]+\.[\d]+\.[\d]+$", opts.version):
    print colored("Version number %s is not in the format X.X.X" % opts.version, "red")
    sys.exit(os.EX_DATAERR)

if not type(opts.columns) == type(2):
    opts.columns    =   int(opts.columns)
    
if opts.columns % 2:
    print colored("Odd numbers of columns are not supported.", "red")
    sys.exit(os.EX_DATAERR)
    
if opts.columns > 48:
    print colored("%d is more columns than we support." % opts.columns, "red")
    sys.exit(os.EX_DATAERR)
    
if opts.debug:
    print "Options"
    for opt in dir(opts):
        if not opt.find('_') == 0 and not opt.find('read') > -1 and not opt.find('ensure') > -1:
            print "  %s: %s" % (opt, str(getattr(opts, opt)))
    print ""
    print "Arguments"
    for i in range(0, len(args)):
        print "  %d: %s" % (i, str(args[i]))
    print ""
    
print colored("Preparing to create version %s\n" % opts.version, "green")

head_matter =   [
    '@charset "utf-8";',
    '',
    '/*',
    ' * smart-grid-core.css',
    ' * Created by Daniel Ryan on 2011-10-09',
    ' * Copyright 2011 Daniel Ryan. All rights reserved.',
    ' * Code developed under a BSD License: https://raw.github.com/dryan/css-smart-grid/master/LICENSE.txt',
    ' * Version: %s' % opts.version,
    ' * Latest update on %s' % date.today().strftime('%Y-%m-%d'),
    ' */',
    '',
]
output      =   [
    '/*',
    ' * Breakpoints:',
    ' * Mobile/Default      -   320px',
    ' * Mobile (landscape)  -   480px',
    ' * Tablet              -   768px',
    ' * Desktop             -   960px',
    ' * Widescreen          -   1200px',
    ' * Widescreen HD       -   1920px',
    ' */',
    '',
    '/*',
    ' * Base container class',
    ' */',
    '.container {',
    '    padding: 0 %dpx;' % (opts.gutter_width / 2),
    '    margin: 0 auto;',
    '    clear: both;',
    '}',
    '',
    '/*',
    ' * contain rows of columns',
    ' */',
    '.row {',
    '    zoom: 1;',
    '    overflow: hidden;',
    '}',
    '',
]

breakpoints =   [
    320,
    480,
    768,
    960,
    1200,
    1920,
]

breakpoint_suffixes =   [
    None,
    None,
    None,
    None,
    'large',
    'hd',
]

container_class                 =   'container'
column_class                    =   'column'
minimum_container_with_columns  =   768

column_sets =   []

outer_gutter_width  =   opts.gutter_width / 2

def get_number_word(num):
    units   =   [
        'zero',
        'one',
        'two',
        'three',
        'four',
        'five',
        'six',
        'seven',
        'eight',
        'nine',
        'ten',
        'eleven',
        'twelve',
        'thirteen',
        'fourteen',
        'fifteen',
        'sixteen',
        'seventeen',
        'nineteen',
    ]
    
    tens    =   [
        '',
        '',
        'twenty',
        'thirty',
        'fourty',
    ]
    
    if num < len(units):
        return units[num]
    output  =   []
    pieces  =   ('%f' % (num / 10.0)).split('.')
    output.append(tens[int(pieces[0])])
    output.append(units[int(pieces[1].strip('0'))])
    
    return "".join(output)
    

for i in range(0, len(breakpoints)):
    breakpoint          =   breakpoints[i]
    is_base             =   (breakpoint == breakpoints[0])
    container_width     =   breakpoint - opts.gutter_width
    column_width        =   (container_width - ((opts.columns - 1) * opts.gutter_width)) / opts.columns
    breakpoint_output   =   []
    ie_output           =   []
    tab_indent          =   "\t" if not is_base else ""
    breakpoint_suffix   =   '.' + breakpoint_suffixes[i] if breakpoint_suffixes[i] else ''

    # see if this breakpoint should also cover additional prefixes
    if breakpoint_suffixes[i]:
        for x in range(i, len(breakpoint_suffixes)):
            if not breakpoint_suffixes[x] == breakpoint_suffix.strip('.'):
                breakpoint_output.append('%s.%s.%s,' % (tab_indent, container_class, breakpoint_suffixes[x]))

    # add the container width for this breakpoint
    breakpoint_output.append('%s.%s%s {' % (tab_indent, container_class, breakpoint_suffix))
    breakpoint_output.append('%s\twidth: %dpx;' % (tab_indent, container_width))
    breakpoint_output.append('%s}' % tab_indent)
    
    # work through the columns
    if breakpoint >= minimum_container_with_columns:
        for col in range(1, opts.columns + 1):
            column_suffix   =   '.' + get_number_word(col) if col > 1 else ''
            col_width       =   col * column_width
            if col > 1:
                col_width   +=  (opts.gutter_width * (col - 1))
            # handle the special case names
            if opts.columns / 2 == col:
                breakpoint_output.append('%s.%s%s .%s.one-half,' % (tab_indent, container_class, breakpoint_suffix, column_class))
            if opts.columns / 4 == col:
                breakpoint_output.append('%s.%s%s .%s.one-fourth,' % (tab_indent, container_class, breakpoint_suffix, column_class))
            if opts.columns / 3 == col:
                breakpoint_output.append('%s.%s%s .%s.one-third,' % (tab_indent, container_class, breakpoint_suffix, column_class))
            if (opts.columns / 4) * 3 == col:
                breakpoint_output.append('%s.%s%s .%s.three-fourths,' % (tab_indent, container_class, breakpoint_suffix, column_class))
            if (opts.columns / 3) * 2 == col:
                breakpoint_output.append('%s.%s%s .%s.two-thirds,' % (tab_indent, container_class, breakpoint_suffix, column_class))
            breakpoint_output.append('%s.%s%s .%s%s {' % (tab_indent, container_class, breakpoint_suffix, column_class, column_suffix))
            breakpoint_output.append('%s\twidth: %dpx;' % (tab_indent, col_width))
            if col == 1 and breakpoint == minimum_container_with_columns:
                breakpoint_output.append('%s\tfloat: left;' % (tab_indent,))
                breakpoint_output.append('%s\tmargin-left: 20px;' % (tab_indent,))
            breakpoint_output.append('%s}' % tab_indent)
            if col == 1 and breakpoint == minimum_container_with_columns:
                breakpoint_output.append('%s.%s%s .%s:first-child,' % (tab_indent, container_class, breakpoint_suffix, column_class))
                breakpoint_output.append('%s.%s%s .%s.first {' % (tab_indent, container_class, breakpoint_suffix, column_class))
                breakpoint_output.append('%s\tmargin-left: 0;' % (tab_indent,))
                breakpoint_output.append('%s}' % tab_indent)
                
    if breakpoint == opts.ie_fallback_width:
        ie_output   =   [
            '/*',
            ' * IE Fallback: %dpx' % breakpoint,
            ' */',
        ]
        for line in breakpoint_output:
            ie_output.append(re.sub(r'^\t', '', line.replace('.%s' % container_class, '.%s .%s' % (opts.ie_fallback_class, container_class))))
            
    if not is_base:
        # wrap these rules in a media query
        breakpoint_output.insert(0, '@media screen and (min-width:%dpx) {' % breakpoint)
        # insert the comments about this breakpoint
        breakpoint_output.insert(0, ' */')
        breakpoint_output.insert(0, ' * Breakpoint: %dpx' % breakpoint)
        breakpoint_output.insert(0, '/*')
        # close the media query
        breakpoint_output.append('}')
    else:
        # insert the comments about this breakpoint
        breakpoint_output.insert(0, ' */')
        breakpoint_output.insert(0, ' * Breakpoint: %dpx' % breakpoint)
        breakpoint_output.insert(0, '/*')

    # push this group onto the main output
    output  =   output + breakpoint_output
    output  =   output + ie_output

if opts.stdout:
    print "\n".join(head_matter)
    print "\n".join(output)
else:
    filename        =   'smart-grid-%d-columns-%d-gutters.css' % (opts.columns, opts.gutter_width)
    if opts.columns == 12 and opts.gutter_width == 20: # our default
        filename    =   'smart-grid.css'
    elif opts.gutter_width == 20: # default gutters with different columns
        filename    =   'smart-grid-%d-columns.css' % opts.columns
    filename_min    =   filename.replace('.css', '.min.css')
    f               =   open(os.path.join(base_dir, filename), 'w')
    f.write("\n".join(head_matter))
    f.write("\n".join(output))
    f.flush()
    f.close()
    f               =   open(os.path.join(base_dir, filename_min), 'w')
    f.write("\n".join(head_matter))
    f.write(cssmin.cssmin("\n".join(output)))
    f.flush()
    f.close()
    
    print colored("%s and %s version %s have been saved." % (filename, filename_min, opts.version), "green")
    print ""
    sys.exit(os.EX_OK)