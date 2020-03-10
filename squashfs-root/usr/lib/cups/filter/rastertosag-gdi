#!/usr/bin/python3 -u
#coding=utf8

# CUPS raster filter for Ricoh Aficio SP1000s
# this printer uses SAG-GDI raster format by Sagem Communication
# licence: GPL
# created by palz <paalzza@gmail.com>
# Feb 2011, Moscow, Russia

from struct import *
import sys
from time import time

# parse command-line parameters
if len(sys.argv)<6:
    exit(1)
jobid = sys.argv[1]
username = sys.argv[2]
jobtitle = sys.argv[3]
try:
    numcopies = int(sys.argv[4])
except:
    numcopies = 1
options = sys.argv[5]
filename='-'
if len(sys.argv)>6:
    filename=sys.argv[6]
if filename=='.' or filename=='-':
    input=sys.stdin.buffer
else:
    input = open(sys.argv[6],'rb')
output = sys.stdout.buffer

def print_stderr(s,newline=True):
    sys.stderr.write(str(s)+('\n' if newline else ''))
    sys.stderr.flush()

#interpret data from CUPS format version 3 supplied via stdin
cups = input.read() # Read all bytes from stdin

sync_word=cups[0:4] # length of sync-word is 4 bytes: "3SaR"
version=cups[0]-48
cups=cups[4:]

dtype={
    'C String': {'b': 's','size': 1},
    'Unsigned Integer': {'b': 'I','size': 4},
    'IEEE Single Precision': {'b': 'f','size': 4},
}

header_length={  # length of page header
    1: 420,
    2: 1796,
    3: 1796,
}

def make_unpack_format(format,begin,end,split_count=1):
    return '<'+(str((end-begin+1)//dtype[format]['size']//split_count)+dtype[format]['b'])*split_count

hdr={
    1: {}, # version 1 header
    2: {}, # version 2-3 header
}
def unpack_header(cups,version):
    # unpack v1 page header
    hdr[1]['MediaClass'], = unpack(make_unpack_format('C String',0,63),cups[0:63+1]) # Media class string
    hdr[1]['MediaColor'], = unpack(make_unpack_format('C String',64,127),cups[64:127+1]) # Media color string
    hdr[1]['MediaType'], = unpack(make_unpack_format('C String',128,191),cups[128:191+1]) # Media type string
    hdr[1]['OutputType'], = unpack(make_unpack_format('C String',192,255),cups[192:255+1]) # Output type string
    hdr[1]['AdvanceDistance'], = unpack(make_unpack_format('Unsigned Integer',256,259),cups[256:259+1]) # 0 to 2<sup>32</sup> - 1 points
    hdr[1]['AdvanceMedia'], = unpack(make_unpack_format('Unsigned Integer',260,263),cups[260:263+1]) # 0 = Never advance roll; 1 = Advance roll after file; 2 = Advance roll after job; 3 = Advance roll after set; 4 = Advance roll after page
    hdr[1]['Collate'], = unpack(make_unpack_format('Unsigned Integer',264,267),cups[264:267+1]) # 0 = do not collate copies; 1 = collate copies
    hdr[1]['CutMedia'], = unpack(make_unpack_format('Unsigned Integer',268,271),cups[268:271+1]) # 0 = Never cut media; 1 = Cut roll after file; 2 = Cut roll after job; 3 = Cut roll after set; 4 = Cut roll after page
    hdr[1]['Duplex'], = unpack(make_unpack_format('Unsigned Integer',272,275),cups[272:275+1]) # 0 = Print single-sided; 1 = Print double-sided
    hdr[1]['HWResolution'] = unpack(make_unpack_format('Unsigned Integer',276,283),cups[276:283+1]) # Horizontal and vertical resolution in dots-per-inch.
    hdr[1]['ImagingBoundingBox'] = unpack(make_unpack_format('Unsigned Integer',284,299),cups[284:299+1]) # Four integers giving the left, bottom, right, and top positions of the page bounding box in points
    hdr[1]['InsertSheet'], = unpack(make_unpack_format('Unsigned Integer',300,303),cups[300:303+1]) # 0 = Do not insert separator sheets; 1 = Insert separator sheets
    hdr[1]['Jog'], = unpack(make_unpack_format('Unsigned Integer',304,307),cups[304:307+1]) # 0 = Do no jog pages; 1 = Jog pages after file; 2 = Jog pages after job; 3 = Jog pages after set
    hdr[1]['LeadingEdge'], = unpack(make_unpack_format('Unsigned Integer',308,311),cups[308:311+1]) # 0 = Top edge is first; 1 = Right edge is first; 2 = Bottom edge is first; 3 = Left edge is first
    hdr[1]['Margins'] = unpack(make_unpack_format('Unsigned Integer',312,319),cups[312:319+1]) # Left and bottom origin of image in points
    hdr[1]['ManualFeed'], = unpack(make_unpack_format('Unsigned Integer',320,323),cups[320:323+1]) # 0 = Do not manually feed media; 1 = Manually feed media
    hdr[1]['MediaPosition'], = unpack(make_unpack_format('Unsigned Integer',324,327),cups[324:327+1]) # Input slot position from 0 to N
    hdr[1]['MediaWeight'], = unpack(make_unpack_format('Unsigned Integer',328,331),cups[328:331+1]) # Media weight in grams per meter squared, 0 = printer default
    hdr[1]['MirrorPrint'], = unpack(make_unpack_format('Unsigned Integer',332,335),cups[332:335+1]) # 0 = Do not mirror prints; 1 = Mirror prints
    hdr[1]['NegativePrint'], = unpack(make_unpack_format('Unsigned Integer',336,339),cups[336:339+1]) # 0 = Do not invert prints; 1 = Invert prints
    hdr[1]['NumCopies'], = unpack(make_unpack_format('Unsigned Integer',340,343),cups[340:343+1]) # 0 to 2<sup>32</sup> - 1, 0 = printer default
    hdr[1]['Orientation'], = unpack(make_unpack_format('Unsigned Integer',344,347),cups[344:347+1]) # 0 = Do not rotate page; 1 = Rotate page counter-clockwise; 2 = Turn page upside down; 3 = Rotate page clockwise
    hdr[1]['OutputFaceUp'], = unpack(make_unpack_format('Unsigned Integer',348,351),cups[348:351+1]) # 0 = Output face down; 1 = Output face up
    hdr[1]['PageSize'] = unpack(make_unpack_format('Unsigned Integer',352,359),cups[352:359+1]) # Width and length in points
    hdr[1]['Separations'], = unpack(make_unpack_format('Unsigned Integer',360,363),cups[360:363+1]) # 0 = Print composite image; 1 = Print color separations
    hdr[1]['TraySwitch'], = unpack(make_unpack_format('Unsigned Integer',364,367),cups[364:367+1]) # 0 = Do not change trays if selected tray is empty; 1 = Change trays if selected tray is empty
    hdr[1]['Tumble'], = unpack(make_unpack_format('Unsigned Integer',368,371),cups[368:371+1]) # 0 = Do not rotate even pages when duplexing; 1 = Rotate even pages when duplexing
    hdr[1]['cupsWidth'], = unpack(make_unpack_format('Unsigned Integer',372,375),cups[372:375+1]) # Width of page image in pixels
    hdr[1]['cupsHeight'], = unpack(make_unpack_format('Unsigned Integer',376,379),cups[376:379+1]) # Height of page image in pixels
    hdr[1]['cupsMediaType'], = unpack(make_unpack_format('Unsigned Integer',380,383),cups[380:383+1]) # Driver-specific 0 to 2<sup>32</sup> - 1
    hdr[1]['cupsBitsPerColor'], = unpack(make_unpack_format('Unsigned Integer',384,387),cups[384:387+1]) # 1, 2, 4, 8 bits for version 1 raster files; 1, 2, 4, 8, and 16 bits for version 2 raster files
    hdr[1]['cupsBitsPerPixel'], = unpack(make_unpack_format('Unsigned Integer',388,391),cups[388:391+1]) # 1 to 32 bits for version 1 raster files; 1 to 64 bits for version 2 raster files
    hdr[1]['cupsBytesPerLine'], = unpack(make_unpack_format('Unsigned Integer',392,395),cups[392:395+1]) # 1 to 2<sup>32</sup> - 1 bytes
    hdr[1]['cupsColorOrder'], = unpack(make_unpack_format('Unsigned Integer',396,399),cups[396:399+1]) # 0 = chunky pixels (CMYK CMYK CMYK); 1 = banded pixels (CCC MMM YYY KKK); 2 = planar pixels (CCC... MMM... YYY... KKK...)
    hdr[1]['cupsColorSpace'], = unpack(make_unpack_format('Unsigned Integer',400,403),cups[400:403+1]) # 0 = gray (device, typically sRGB-based); 1 = RGB (device, typically sRGB); 2 = RGBA (device, typically sRGB); 3 = black; 4 = CMY; 5 = YMC; 6 = CMYK; 7 = YMCK; 8 = KCMY; 9 = KCMYcm; 10 = GMCK; 11 = GMCS; 12 = WHITE; 13 = GOLD; 14 = SILVER; 15 = CIE XYZ; 16 = CIE Lab; 17 = RGBW (sRGB); 18 = sGray (gray using sRGB gamma/white point); 19 = sRGB; 20 = AdobeRGB; 32 = ICC1 (CIE Lab with hint for 1 color); 33 = ICC2 (CIE Lab with hint for 2 colors); 34 = ICC3 (CIE Lab with hint for 3 colors); 35 = ICC4 (CIE Lab with hint for 4 colors); 36 = ICC5 (CIE Lab with hint for 5 colors); 37 = ICC6 (CIE Lab with hint for 6 colors); 38 = ICC7 (CIE Lab with hint for 7 colors); 39 = ICC8 (CIE Lab with hint for 8 colors); 40 = ICC9 (CIE Lab with hint for 9 colors); 41 = ICCA (CIE Lab with hint for 10 colors); 42 = ICCB (CIE Lab with hint for 11 colors); 43 = ICCC (CIE Lab with hint for 12 colors); 44 = ICCD (CIE Lab with hint for 13 colors); 45 = ICCE (CIE Lab with hint for 14 colors); 46 = ICCF (CIE Lab with hint for 15 colors); 48 = Device1 (DeviceN for 1 color); 48 = Device2 (DeviceN for 2 colors); 48 = Device3 (DeviceN for 3 colors); 48 = Device4 (DeviceN for 4 colors); 48 = Device5 (DeviceN for 5 colors); 48 = Device6 (DeviceN for 6 colors); 48 = Device7 (DeviceN for 7 colors); 48 = Device8 (DeviceN for 8 colors); 48 = Device9 (DeviceN for 9 colors); 48 = DeviceA (DeviceN for 10 colors); 48 = DeviceB (DeviceN for 11 colors); 48 = DeviceC (DeviceN for 12 colors); 48 = DeviceD (DeviceN for 13 colors); 48 = DeviceE (DeviceN for 14 colors); 48 = DeviceF (DeviceN for 15 colors)
    hdr[1]['cupsCompression'], = unpack(make_unpack_format('Unsigned Integer',404,407),cups[404:407+1]) # Driver-specific 0 to 2<sup>32</sup> - 1
    hdr[1]['cupsRowCount'], = unpack(make_unpack_format('Unsigned Integer',408,411),cups[408:411+1]) # Driver-specific 0 to 2<sup>32</sup> - 1
    hdr[1]['cupsRowFeed'], = unpack(make_unpack_format('Unsigned Integer',412,415),cups[412:415+1]) # Driver-specific 0 to 2<sup>32</sup> - 1
    hdr[1]['cupsRowStep'], = unpack(make_unpack_format('Unsigned Integer',416,419),cups[416:419+1]) # Driver-specific 0 to 2<sup>32</sup> - 1

    # unpack v2 page header
    if(version>1):
        hdr[2]['cupsNumColors'], = unpack(make_unpack_format('Unsigned Integer',420,423),cups[420:423+1]) # 1 to 6 colors
        hdr[2]['cupsBorderlessScalingFactor'], = unpack(make_unpack_format('IEEE Single Precision',424,427),cups[424:427+1]) # 0.0 or 1.0 or greater
        hdr[2]['cupsPageSize'] = unpack(make_unpack_format('IEEE Single Precision',428,435),cups[428:435+1]) # Width and length in points
        hdr[2]['cupsImagingBBox'] = unpack(make_unpack_format('IEEE Single Precision',436,451),cups[436:451+1]) # Four floating point numbers giving the left, bottom, right, and top positions of the page bounding box in points
        hdr[2]['cupsInteger'] = unpack(make_unpack_format('Unsigned Integer',452,515),cups[452:515+1]) # 16 driver-defined integer values
        hdr[2]['cupsReal'] = unpack(make_unpack_format('IEEE Single Precision',516,579),cups[516:579+1]) # 16 driver-defined floating point values
        hdr[2]['cupsString'] = unpack(make_unpack_format('C String',580,1603,16),cups[580:1603+1]) # 16 driver-defined strings
        hdr[2]['cupsMarkerType'], = unpack(make_unpack_format('C String',1604,1667),cups[1604:1667+1]) # Ink/toner type string
        hdr[2]['cupsRenderingIntent'], = unpack(make_unpack_format('C String',1668,1731),cups[1668:1731+1]) # Color rendering intent string
        hdr[2]['cupsPageSizeName'], = unpack(make_unpack_format('C String',1732,1795),cups[1732:1795+1]) # Page size name/keyword string from PPD
    
    return hdr

page_data=''

def get_cups_page():
    global cups,page_data
    if len(cups):
        hdr=unpack_header(cups[:header_length[version]],version)

        print_stderr('cupsWidth x cupsHeight: '+str(hdr[1]['cupsWidth'])+' x '+str(hdr[1]['cupsHeight']))
        print_stderr('cupsBytesPerLine: '+str(hdr[1]['cupsBytesPerLine']))
        print_stderr('cupsBitsPerPixel: '+str(hdr[1]['cupsBitsPerPixel']))
        print_stderr('cupsColorOrder: '+str(hdr[1]['cupsColorOrder']))
        print_stderr('page size in bytes = '+str(hdr[1]['cupsBytesPerLine']*hdr[1]['cupsHeight']))

        page_data=cups[header_length[version]:header_length[version]+hdr[1]['cupsBytesPerLine']*hdr[1]['cupsHeight']]
        cups=cups[header_length[version]+len(page_data):]
        return True
    else:
        return False

def make_bytes():
    ret=[]
    for byte in range(256):
        ret.append([
            1 if byte&0b10000000 else 0,
            1 if byte&0b01000000 else 0,
            1 if byte&0b00100000 else 0,
            1 if byte&0b00010000 else 0,
            1 if byte&0b00001000 else 0,
            1 if byte&0b00000100 else 0,
            1 if byte&0b00000010 else 0,
            1 if byte&0b00000001 else 0,
        ])
    return ret

bytes = make_bytes()
def get_cups_line(y):
    numbytes=hdr[1]['cupsBytesPerLine']
    w=hdr[1]['cupsWidth']
    line=unpack('<'+str(numbytes)+'B',page_data[y*numbytes:(y+1)*numbytes])
    ret=[]
    extend=ret.extend
    for x in range(0,w//8):
        extend(bytes[line[x]])
    if w%8:
        extend(bytes[line[w//8]][:w%8])
    return ret

FORMAT_WIDTH=0
FORMAT_HEIGHT=1
FORMAT_LINEFILL=2
FORMAT_INDEX=3
formats = {   
    'A4': (0x129A,0x1A7A,0x9A4A,0x0000),
    'A5': (0x0CE2,0x1276,0xA233,0x0004),
    'A6': (0x08E9,0x0CBE,0xA923,0x000E),
    'Letter': (0x1324,0x18DC,0xA44C,0x0001),
    'Legal': (0x1324,0x1FE4,0xA44C,0x0002),
    'B5': (0x1006,0x16CC,0x8640,0x0005),
    'B6': (0x0B14,0x0FE2,0x942C,0x000D),
    'Monarch': (0x0850,0x10A8,0x9021,0x0008),
    # (width,height,linefill,index,)
    # LINEFILL is created by common rule 0x129A = 0x9A + 64 * 0x4A
}

def begin_document():
    output.write(pack(
        '>76sbbHHI',
        b') SAG-GDI RL;0;0;Comment Copyright Sagem Communication 2005. Version 1.0.0.0',
        0x0D,0x0A,
        0x1000,0x0200,
        0
    ))

def end_document():
    output.write(pack('>3H',0x1400,0,0))

format = 'A4'
def begin_page(page_format='A4',numcopies=1,toner_economy=False):
    if not (page_format in formats):
      page_format='A4'
    global linefill,format
    format=page_format
    linefill=formats[format][FORMAT_LINEFILL]
    output.write(pack(
        '<II4H2B3B',
        0x000F0011,
        int(hdr[1]['MediaPosition']),
        0x0404,0,formats[format][FORMAT_WIDTH],formats[format][FORMAT_HEIGHT],
        formats[format][FORMAT_INDEX],int(hdr[1]['cupsMediaType']),
        numcopies,0,1 if toner_economy else 0
    ))

def end_page():
    output.write(pack('>3H',0x1300,0,0))

current_block_data=''
current_line_length=0
def begin_block():
    global current_block_data
    current_block_data=b''

def get_block_size():
    return len(current_block_data)

def end_block():
    output.write(pack('<3H',0x0012,get_block_size(),0)+current_block_data)

def write_px_data(col,length):
    if length<=0:
        return

    color = 1 if col else 0
    color_bit = color << 6
    first_byte = length%64
    second_byte = length//64
    two_bytes_bit = 0b10000000 if second_byte else 0b00000000
    
    px_data=pack('>B', two_bytes_bit | color_bit | first_byte)
    if second_byte:
        px_data=px_data+pack('>B',second_byte)

    # start new block of commands if previous is full
    if len(px_data)+get_block_size()>0xFF:
        end_block()
        begin_block()
        
    global current_line_length,current_block_data
    current_block_data+=px_data
    current_line_length+=length

def fill_line():
    global current_line_length
    write_px_data(0,formats[format][FORMAT_WIDTH]-current_line_length)
    current_line_length=0

def write_cups():
    w,h=min(hdr[1]['cupsWidth'],formats[format][FORMAT_WIDTH]),min(hdr[1]['cupsHeight'],formats[format][FORMAT_HEIGHT])
    t=time()
    for y in range(h):
        if y%(h//15)==0:
            print_stderr('%d%% '%(int(float(y)/h*100),),False)

        yline=get_cups_line(y)
        lastcol=yline[0]
        lastcolidx=0
        for x in range(1,w):
            currcol=yline[x] # 1 means black pixel
            if (currcol!=lastcol):
                write_px_data(lastcol,x-lastcolidx)
                lastcol=currcol
                lastcolidx=x
        write_px_data(lastcol,w-lastcolidx)
        fill_line() # fills rest of the line and resets current_line_length
    if h<formats[format][FORMAT_HEIGHT]:
        for y in range(h,formats[format][FORMAT_HEIGHT]):
            fill_line()
    print_stderr('100%%.\nDone in %.3f seconds.'%(time()-t,))

begin_document()

curr_page_number=0
while get_cups_page():
    begin_page(hdr[2]['cupsPageSizeName'][:2],numcopies=numcopies)
    begin_block()
    
    curr_page_number+=1
    print_stderr('Rendering page %i'%(curr_page_number,))
    write_cups()

    end_block()
    end_page()

end_document()