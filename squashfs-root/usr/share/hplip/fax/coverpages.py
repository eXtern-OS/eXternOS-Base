# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", SyntaxWarning)
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import Preformatted, Image, HRFlowable
from reportlab.platypus.doctemplate import *
#from reportlab.rl_config import TTFSearchPath
from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.pagesizes import letter, legal, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
#from reportlab.pdfbase import pdfmetrics
#from reportlab.pdfbase.ttfonts import TTFont
from time import localtime, strftime
#import warnings
warnings.simplefilter('default', DeprecationWarning)
warnings.simplefilter("default", SyntaxWarning)

if __name__ ==  "__main__":
    import sys
    sys.path.append("..")

from base.g import *
from base import utils

PAGE_SIZE_LETTER = 'letter'
PAGE_SIZE_LEGAL = 'legal'
PAGE_SIZE_A4 = 'a4'


def escape(s):
    return s.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")


def createStandardCoverPage(page_size=PAGE_SIZE_LETTER,
                            total_pages=1,
                            recipient_name='',
                            recipient_phone='',
                            recipient_fax='',
                            sender_name='',
                            sender_phone='',
                            sender_fax='',
                            sender_email='',
                            regarding='',
                            message='',
                            preserve_formatting=False,
                            output=None):

    s = getSampleStyleSheet()

    story = []

    #print prop.locale
    #TTFSearchPath.append('/usr/share/fonts/truetype/arphic')
    #pdfmetrics.registerFont(TTFont('UMing', 'uming.ttf'))

    ps = ParagraphStyle(name="title",
                        parent=None,
                        fontName='helvetica-bold',
                        #fontName='STSong-Light',
                        #fontName = 'UMing',
                        fontSize=72,
                        )

    story.append(Paragraph("FAX", ps))

    story.append(Spacer(1, inch))

    ps = ParagraphStyle(name='normal',
                        fontName='Times-Roman',
                        #fontName='STSong-Light',
                        #fontName='UMing',
                        fontSize=12)

    recipient_name_label = Paragraph("To:", ps)
    recipient_name_text = Paragraph(escape(recipient_name[:64]), ps)

    recipient_fax_label = Paragraph("Fax:", ps)
    recipient_fax_text = Paragraph(escape(recipient_fax[:64]), ps)

    recipient_phone_label = Paragraph("Phone:", ps)
    recipient_phone_text = Paragraph(escape(recipient_phone[:64]), ps)

    sender_name_label = Paragraph("From:", ps)
    sender_name_text = Paragraph(escape(sender_name[:64]), ps)

    sender_phone_label = Paragraph("Phone:", ps)
    sender_phone_text = Paragraph(escape(sender_phone[:64]), ps)

    sender_email_label = Paragraph("Email:", ps)
    sender_email_text = Paragraph(escape(sender_email[:64]), ps)

    regarding_label = Paragraph("Regarding:", ps)
    regarding_text = Paragraph(escape(regarding[:128]), ps)

    date_time_label = Paragraph("Date:", ps)
    date_time_text = Paragraph(strftime("%a, %d %b %Y %H:%M:%S (%Z)", localtime()), ps)

    total_pages_label = Paragraph("Total Pages:", ps)
    total_pages_text = Paragraph("%d" % total_pages, ps)

    data = [[recipient_name_label, recipient_name_text, sender_name_label, sender_name_text],
            [recipient_fax_label, recipient_fax_text, sender_phone_label, sender_phone_text],
            [date_time_label, date_time_text, sender_email_label, sender_email_text],
            [regarding_label, regarding_text, total_pages_label, total_pages_text]]

    LIST_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                             #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                             #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                             ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ])

    story.append(HRFlowable(width='100%', color='black'))

    story.append(Table(data, style=LIST_STYLE))

    if message:
        MSG_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                                 #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                                 #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                                 ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 ('SPAN', (-2, 1), (-1, -1)),
                                ])

        story.append(HRFlowable(width='100%', color='black'))
        story.append(Spacer(1, 0.5*inch))

        if preserve_formatting:
            message = '\n'.join(message[:2048].splitlines()[:32])

            data = [[Paragraph("Comments/Notes:", ps), ''],
                    [Preformatted(escape(message), ps), ''],]
        else:
            data = [[Paragraph("Comments/Notes:", ps), ''],
                    [Paragraph(escape(message[:2048]), ps), ''],]

        story.append(HRFlowable(width='100%', color='black'))
        story.append(Table(data, style=MSG_STYLE))
        story.append(HRFlowable(width='100%', color='black'))

    if page_size == PAGE_SIZE_LETTER:
        pgsz = letter
    elif page_size == PAGE_SIZE_LEGAL:
        pgsz = legal
    else:
        pgsz = A4

    if output is None:
        f_fd, f = utils.make_temp_file()
    else:
        f = output

    doc = SimpleDocTemplate(f, pagesize=pgsz)
    doc.build(story)

    return f


def createConfidentialCoverPage(page_size=PAGE_SIZE_LETTER,
                            total_pages=1,
                            recipient_name='',
                            recipient_phone='',
                            recipient_fax='',
                            sender_name='',
                            sender_phone='',
                            sender_fax='',
                            sender_email='',
                            regarding='',
                            message='',
                            preserve_formatting=False,
                            output=None):

    s = getSampleStyleSheet()

    story = []

    story.append(Image(os.path.join(prop.image_dir, 'other', 'confidential_title.png')))
    story.append(Spacer(1, inch))
    story.append(HRFlowable(width='100%', color='black'))

    ps = ParagraphStyle(name='normal',
                        fontName='Times-Roman',
                        #fontName='STSong-Light',
                        #fontName='UMing',
                        fontSize=12)

    recipient_name_label = Paragraph("To:", ps)
    recipient_name_text = Paragraph(escape(recipient_name[:64]), ps)

    recipient_fax_label = Paragraph("Fax:", ps)
    recipient_fax_text = Paragraph(escape(recipient_fax[:64]), ps)

    recipient_phone_label = Paragraph("Phone:", ps)
    recipient_phone_text = Paragraph(escape(recipient_phone[:64]), ps)

    sender_name_label = Paragraph("From:", ps)
    sender_name_text = Paragraph(escape(sender_name[:64]), ps)

    sender_phone_label = Paragraph("Phone:", ps)
    sender_phone_text = Paragraph(escape(sender_phone[:64]), ps)

    sender_email_label = Paragraph("Email:", ps)
    sender_email_text = Paragraph(escape(sender_email[:64]), ps)

    regarding_label = Paragraph("Regarding:", ps)
    regarding_text = Paragraph(escape(regarding[:128]), ps)

    date_time_label = Paragraph("Date:", ps)
    date_time_text = Paragraph(strftime("%a, %d %b %Y %H:%M:%S (%Z)", localtime()), ps)

    total_pages_label = Paragraph("Total Pages:", ps)
    total_pages_text = Paragraph("%d" % total_pages, ps)

    data = [[recipient_name_label, recipient_name_text],
            [recipient_fax_label, recipient_fax_text],
            ['', ''],
            [sender_name_label, sender_name_text],
            [sender_phone_label, sender_phone_text],
            [sender_email_label, sender_email_text],
            ['', ''],
            [date_time_label, date_time_text],
            [total_pages_label, total_pages_text],
            [regarding_label, regarding_text],]

    LIST_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                             #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                             #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                             ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ])


    story.append(Table(data, style=LIST_STYLE))
    story.append(HRFlowable(width='100%', color='black'))

    if message:
        MSG_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                                 #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                                 #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                                 ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 #('SPAN', (-2, 1), (-1, -1)),
                                ])

        #story.append(HRFlowable(width='100%', color='black'))
        story.append(Spacer(1, 0.5*inch))

#        if preserve_formatting:
#            message = '\n'.join(message[:2048].splitlines()[:32])
#
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Preformatted(escape(message), ps)],]
#        else:
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Paragraph(escape(message[:2048]), ps), ''],]
#
#        #story.append(HRFlowable(width='100%', color='black'))
#        #story.append(Table(data, style=MSG_STYLE))

        if preserve_formatting:
            message = '\n'.join(message[:2048].splitlines()[:32])
            story.append(Preformatted(escape(message), ps))
        else:
            story.append(Paragraph(escape(message), ps))


    if page_size == PAGE_SIZE_LETTER:
        pgsz = letter
    elif page_size == PAGE_SIZE_LEGAL:
        pgsz = legal
    else:
        pgsz = A4

    if output is None:
        f_fd, f = utils.make_temp_file()
    else:
        f = output

    doc = SimpleDocTemplate(f, pagesize=pgsz)
    doc.build(story)

    return f


def createGenericCoverPage(page_size=PAGE_SIZE_LETTER,
                            total_pages=1,
                            recipient_name='',
                            recipient_phone='',
                            recipient_fax='',
                            sender_name='',
                            sender_phone='',
                            sender_fax='',
                            sender_email='',
                            regarding='',
                            message='',
                            preserve_formatting=False,
                            output=None):

    s = getSampleStyleSheet()

    story = []

    i = Image(os.path.join(prop.image_dir, 'other', 'generic_title.png'), width=250, height=147)
    i.hAlign = 'LEFT'
    story.append(i)
    #story.append(Spacer(1, inch))
    story.append(HRFlowable(width='100%', color='black'))

    ps = ParagraphStyle(name='normal',
                        fontName='Times-Roman',
                        #fontName='STSong-Light',
                        #fontName='UMing',
                        fontSize=12)

    recipient_name_label = Paragraph("To:", ps)
    recipient_name_text = Paragraph(escape(recipient_name[:64]), ps)

    recipient_fax_label = Paragraph("Fax:", ps)
    recipient_fax_text = Paragraph(escape(recipient_fax[:64]), ps)

    recipient_phone_label = Paragraph("Phone:", ps)
    recipient_phone_text = Paragraph(escape(recipient_phone[:64]), ps)

    sender_name_label = Paragraph("From:", ps)
    sender_name_text = Paragraph(escape(sender_name[:64]), ps)

    sender_phone_label = Paragraph("Phone:", ps)
    sender_phone_text = Paragraph(escape(sender_phone[:64]), ps)

    sender_email_label = Paragraph("Email:", ps)
    sender_email_text = Paragraph(escape(sender_email[:64]), ps)

    regarding_label = Paragraph("Regarding:", ps)
    regarding_text = Paragraph(escape(regarding[:128]), ps)

    date_time_label = Paragraph("Date:", ps)
    date_time_text = Paragraph(strftime("%a, %d %b %Y %H:%M:%S (%Z)", localtime()), ps)

    total_pages_label = Paragraph("Total Pages:", ps)
    total_pages_text = Paragraph("%d" % total_pages, ps)

    data = [[recipient_name_label, recipient_name_text],
            [recipient_fax_label, recipient_fax_text],
            ['', ''],
            [sender_name_label, sender_name_text],
            [sender_phone_label, sender_phone_text],
            [sender_email_label, sender_email_text],
            ['', ''],
            [date_time_label, date_time_text],
            [total_pages_label, total_pages_text],
            [regarding_label, regarding_text],]

    LIST_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                             #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                             #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                             ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ])


    story.append(Table(data, style=LIST_STYLE))
    story.append(HRFlowable(width='100%', color='black'))

    if message:
        MSG_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                                 #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                                 #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                                 ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 #('SPAN', (-2, 1), (-1, -1)),
                                ])

        #story.append(HRFlowable(width='100%', color='black'))
        story.append(Spacer(1, 0.5*inch))

#        if preserve_formatting:
#            message = '\n'.join(message[:2048].splitlines()[:32])
#
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Preformatted(escape(message), ps)],]
#        else:
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Paragraph(escape(message[:2048]), ps), ''],]
#
#        #story.append(HRFlowable(width='100%', color='black'))
#        #story.append(Table(data, style=MSG_STYLE))

        if preserve_formatting:
            message = '\n'.join(message[:2048].splitlines()[:32])
            story.append(Preformatted(escape(message), ps))
        else:
            story.append(Paragraph(escape(message), ps))

    #

    if page_size == PAGE_SIZE_LETTER:
        pgsz = letter
    elif page_size == PAGE_SIZE_LEGAL:
        pgsz = legal
    else:
        pgsz = A4

    if output is None:
        f_fd, f = utils.make_temp_file()
    else:
        f = output

    doc = SimpleDocTemplate(f, pagesize=pgsz)
    doc.build(story)

    return f


def createUrgentCoverPage(page_size=PAGE_SIZE_LETTER,
                            total_pages=1,
                            recipient_name='',
                            recipient_phone='',
                            recipient_fax='',
                            sender_name='',
                            sender_phone='',
                            sender_fax='',
                            sender_email='',
                            regarding='',
                            message='',
                            preserve_formatting=False,
                            output=None):

    s = getSampleStyleSheet()

    story = []
    i = Image(os.path.join(prop.image_dir, 'other', 'urgent_title.png'), width=424, height=92)
    i.hAlign = 'LEFT'
    story.append(i)
    story.append(Spacer(1, inch))
    story.append(HRFlowable(width='100%', color='black'))

    ps = ParagraphStyle(name='normal',
                        fontName='Times-Roman',
                        #fontName='STSong-Light',
                        #fontName='UMing',
                        fontSize=12)

    recipient_name_label = Paragraph("To:", ps)
    recipient_name_text = Paragraph(escape(recipient_name[:64]), ps)

    recipient_fax_label = Paragraph("Fax:", ps)
    recipient_fax_text = Paragraph(escape(recipient_fax[:64]), ps)

    recipient_phone_label = Paragraph("Phone:", ps)
    recipient_phone_text = Paragraph(escape(recipient_phone[:64]), ps)

    sender_name_label = Paragraph("From:", ps)
    sender_name_text = Paragraph(escape(sender_name[:64]), ps)

    sender_phone_label = Paragraph("Phone:", ps)
    sender_phone_text = Paragraph(escape(sender_phone[:64]), ps)

    sender_email_label = Paragraph("Email:", ps)
    sender_email_text = Paragraph(escape(sender_email[:64]), ps)

    regarding_label = Paragraph("Regarding:", ps)
    regarding_text = Paragraph(escape(regarding[:128]), ps)

    date_time_label = Paragraph("Date:", ps)
    date_time_text = Paragraph(strftime("%a, %d %b %Y %H:%M:%S (%Z)", localtime()), ps)

    total_pages_label = Paragraph("Total Pages:", ps)
    total_pages_text = Paragraph("%d" % total_pages, ps)

    data = [[recipient_name_label, recipient_name_text],
            [recipient_fax_label, recipient_fax_text],
            ['', ''],
            [sender_name_label, sender_name_text],
            [sender_phone_label, sender_phone_text],
            [sender_email_label, sender_email_text],
            ['', ''],
            [date_time_label, date_time_text],
            [total_pages_label, total_pages_text],
            [regarding_label, regarding_text],]

    LIST_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                             #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                             #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                             ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ])


    story.append(Table(data, style=LIST_STYLE))
    story.append(HRFlowable(width='100%', color='black'))

    if message:
        MSG_STYLE = TableStyle([#('LINEABOVE', (0,0), (-1,0), 2, colors.black),
                                 #('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
                                 #('LINEBELOW', (0,-1), (-1,-1), 2, colors.black),
                                 ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 #('SPAN', (-2, 1), (-1, -1)),
                                ])

        #story.append(HRFlowable(width='100%', color='black'))
        story.append(Spacer(1, 0.5*inch))

#        if preserve_formatting:
#            message = '\n'.join(message[:2048].splitlines()[:32])
#
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Preformatted(escape(message), ps)],]
#        else:
#            data = [#[Paragraph("Comments/Notes:", ps), ''],
#                    [Paragraph(escape(message[:2048]), ps), ''],]
#
#        #story.append(HRFlowable(width='100%', color='black'))
#        #story.append(Table(data, style=MSG_STYLE))

        if preserve_formatting:
            message = '\n'.join(message[:2048].splitlines()[:32])
            story.append(Preformatted(escape(message), ps))
        else:
            story.append(Paragraph(escape(message), ps))


    if page_size == PAGE_SIZE_LETTER:
        pgsz = letter
    elif page_size == PAGE_SIZE_LEGAL:
        pgsz = legal
    else:
        pgsz = A4

    if output is None:
        f_fd, f = utils.make_temp_file()
    else:
        f = output

    doc = SimpleDocTemplate(f, pagesize=pgsz)
    doc.build(story)

    return f


#            { "name" : (function, "thumbnail.png"), ... }
COVERPAGES = { "basic": (createStandardCoverPage, 'standard_coverpage.png'),
               "confidential": (createConfidentialCoverPage, 'confidential_coverpage.png'),
               "generic": (createGenericCoverPage, "generic_coverpage.png"),
               "urgent": (createUrgentCoverPage, "urgent_coverpage.png"),
             }


if __name__ ==  "__main__":
    createUrgentCoverPage(page_size=PAGE_SIZE_LETTER,
                                total_pages=1,
                                recipient_name='Trex',
                                recipient_phone='+1 234-567-8912',
                                recipient_fax='+1 432 123 1234',
                                sender_name='Don',
                                sender_phone='+1 234 432 1234',
                                sender_fax='+1 567 876 5123 ',
                                sender_email='test@hplip.sf.net',
                                regarding='Some sorta stuff',
                                message="""Some HP printers require proprietary software technologies to allow full access to printer features and performance. These technologies cannot be open sourced. Because of this, HP uses a binary plug-in for these printers that work in conjunction with our Linux Open Source Printing Software to improve the printing experience for HP’s Linux Printing Customers. This binary plug-in requires the user to read and agree to a license agreement at the time of driver installation.  There is a single plug-in file (for each HPLIP release) for all plug-in enabled devices.""",
                                preserve_formatting=False,
                                output="output.pdf")


