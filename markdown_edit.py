#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import SimpleHTTPServer
import SocketServer
import urllib2
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SimpleHTTPServer import BaseHTTPServer
from BaseHTTPServer import HTTPServer
import markdown
import webbrowser
import traceback
import logging
from logging import DEBUG, INFO, CRITICAL
import codecs
import base64
import optparse

logger =  logging.getLogger('MARKDOWN_EDITOR')

HTML_TEMPLATE = """
<html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="content-type">
        <title>Markdown Editor</title>

        <script>
            function updateHtmlPreview()
            {
            var xmlhttp;
            if (window.XMLHttpRequest)
              {// code for IE7+, Firefox, Chrome, Opera, Safari
              xmlhttp=new XMLHttpRequest();
              }
            else
              {// code for IE6, IE5
              xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
              }
            xmlhttp.onreadystatechange=function()
              {
              if (xmlhttp.readyState==4 && xmlhttp.status==200)
                {
                document.getElementById("html_result").innerHTML=xmlhttp.responseText;
                }
              }
            xmlhttp.open("POST","ajaxUpdate",false);
            xmlhttp.send(document.getElementById("markdown_input").value);
            }

        </script>
        <style>
            %(mail_style)s
        </style>
    </head>

    <body style="background-color: rgb(204, 204, 204);">
        <form method="post" action="/" name="markdown_input">
        
        %(html_head)s

        <table style="text-align: left; width: 100%%;" border="0" cellpadding="2" cellspacing="2">
            <tbody>
            <tr> <!-- ACTIONS -->
                <td>
                    %(in_actions)s
                </td>
                <td>
                    %(out_actions)s
                </td>
            </tr>
            <tr> <!-- MARKDOWN INPUT and HTML PREVIEW -->
                <td style="vertical-align: top; width: 1px;">
                    <textarea onKeyUp="updateHtmlPreview()" id="markdown_input" cols="80" rows="30" name="markdown_text" style="min-height: 400px;">%(markdown_input)s</textarea>
                </td>
                <td style="vertical-align: top; width: 100%%;">
                    <div class="markdown-body" id="html_result" style="border-style: inset; padding-right: 4px; padding-left: 4px; background-color: white; display: block; min-height: 400px;">%(html_result)s</div>
                </td>
            </tr>

            </tbody>
        </table>

        </form>
    </body>
</html>
"""

ACTION_TEMPLATE = '<input type="submit" name="SubmitAction" value="%s">'

OUTPUT_HTML_ENVELOPE = """<html>
<head>
<style type="text/css">
%s
</style>
</head>
<body>
<div class="markdown-body">
%s
</div>
</body>
</html>
"""

DOC_STYLE = """

body {
background-color: #FFFFFF;
}

tt, code, pre {
font-family: Consolas, "Liberation Mono", Courier, monospace;
font-size: 12px;
}

table {
border-collapse: collapse;
border-spacing: 0;
}

* {
-moz-box-sizing: border-box;
box-sizing: border-box;
}

.markdown-body{
font-family: sans-serif;
font-size:15px;
line-height:1.7;
overflow:hidden;
word-wrap:break-word
}

.markdown-body>*:first-child{
margin-top:0 !important
}

.markdown-body>*:last-child{
margin-bottom:0 !important
}

.markdown-body a.absent{
color:#c00
}

.markdown-body a.anchor{
display:block;
padding-right:6px;
padding-left:30px;
margin-left:-30px;
cursor:pointer;
position:absolute;
top:0;
left:0;
bottom:0
}

.markdown-body a.anchor:focus{
outline:none
}

.markdown-body h1,.markdown-body h2,.markdown-body h3,.markdown-body h4,.markdown-body h5,.markdown-body h6{
margin:1em 0 15px;
padding:0;
font-weight:bold;
line-height:1.7;
cursor:text;
position:relative
}

.markdown-body h1 .octicon-link,.markdown-body h2 .octicon-link,.markdown-body h3 .octicon-link,.markdown-body h4 .octicon-link,.markdown-body h5 .octicon-link,.markdown-body h6 .octicon-link{
display:none;
color:#000
}

.markdown-body h1:hover a.anchor,.markdown-body h2:hover a.anchor,.markdown-body h3:hover a.anchor,.markdown-body h4:hover a.anchor,.markdown-body h5:hover a.anchor,.markdown-body h6:hover a.anchor{
text-decoration:none;
line-height:1;
padding-left:8px;
margin-left:-30px;
top:15%
}

.markdown-body h1:hover a.anchor .octicon-link,.markdown-body h2:hover a.anchor .octicon-link,.markdown-body h3:hover a.anchor .octicon-link,.markdown-body h4:hover a.anchor .octicon-link,.markdown-body h5:hover a.anchor .octicon-link,.markdown-body h6:hover a.anchor .octicon-link{
display:inline-block
}

.markdown-body h1 tt,.markdown-body h1 code,.markdown-body h2 tt,.markdown-body h2 code,.markdown-body h3 tt,.markdown-body h3 code,.markdown-body h4 tt,.markdown-body h4 code,.markdown-body h5 tt,.markdown-body h5 code,.markdown-body h6 tt,.markdown-body h6 code{
font-size:inherit
}

.markdown-body h1{
font-size:2.5em;
border-bottom:1px solid #ddd
}

.markdown-body h2{
font-size:2em;
border-bottom:1px solid #eee
}

.markdown-body h3{
font-size:1.5em
}

.markdown-body h4{
font-size:1.2em
}

.markdown-body h5{
font-size:1em
}

.markdown-body h6{
color:#777;
font-size:1em
}

.markdown-body p,.markdown-body blockquote,.markdown-body ul,.markdown-body ol,.markdown-body dl,.markdown-body table,.markdown-body pre{
margin:15px 0
}

.markdown-body hr {
background: rgba(216, 216, 216, 1);
border: 0 none;
color: #ccc;
height: 2px;
padding: 0;
margin: 15px 0;
}

.markdown-body ul,.markdown-body ol{
padding-left:30px
}

.markdown-body ul.no-list,.markdown-body ol.no-list{
list-style-type:none;
padding:0
}

.markdown-body ul ul,.markdown-body ul ol,.markdown-body ol ol,.markdown-body ol ul{
margin-top:0;
margin-bottom:0
}

.markdown-body dl{
padding:0
}

.markdown-body dl dt{
font-size:14px;
font-weight:bold;
font-style:italic;
padding:0;
margin-top:15px
}

.markdown-body dl dd{
margin-bottom:15px;
padding:0 15px
}

.markdown-body blockquote{
border-left:4px solid #DDD;
padding:0 15px;
color:#777
}

.markdown-body blockquote>:first-child{
margin-top:0px
}

.markdown-body blockquote>:last-child{
margin-bottom:0px
}

.markdown-body table{
/* width:100%; */
overflow:auto;
display:block
}

.markdown-body table th{
font-weight:bold
}

.markdown-body table th,.markdown-body table td{
border:1px solid #ddd;
padding:6px 13px
}

.markdown-body table tr{
border-top:1px solid #ccc;
background-color:#fff
}

.markdown-body table tr:nth-child(2n){
background-color:#f8f8f8
}

.markdown-body img{
max-width:100%;
-moz-box-sizing:border-box;
box-sizing:border-box
}

.markdown-body span.frame{
display:block;
overflow:hidden
}

.markdown-body span.frame>span{
border:1px solid #ddd;
display:block;
float:left;
overflow:hidden;
margin:13px 0 0;
padding:7px;
width:auto
}

.markdown-body span.frame span img{
display:block;
float:left
}

.markdown-body span.frame span span{
clear:both;
color:#333;
display:block;
padding:5px 0 0
}

.markdown-body span.align-center{
display:block;
overflow:hidden;
clear:both
}

.markdown-body span.align-center>span{
display:block;
overflow:hidden;
margin:13px auto 0;
text-align:center
}

.markdown-body span.align-center span img{
margin:0 auto;
text-align:center
}

.markdown-body span.align-right{
display:block;
overflow:hidden;
clear:both
}

.markdown-body span.align-right>span{
display:block;
overflow:hidden;
margin:13px 0 0;
text-align:right
}

.markdown-body span.align-right span img{
margin:0;
text-align:right
}

.markdown-body span.float-left{
display:block;
margin-right:13px;
overflow:hidden;
float:left
}

.markdown-body span.float-left span{
margin:13px 0 0
}

.markdown-body span.float-right{
display:block;
margin-left:13px;
overflow:hidden;
float:right
}

.markdown-body span.float-right>span{
display:block;
overflow:hidden;
margin:13px auto 0;
text-align:right
}

.markdown-body code,.markdown-body tt{
margin:0;
border:1px solid #ddd;
background-color:#f8f8f8;
border-radius:3px;
max-width:100%;
display:inline-block;
overflow:auto;
vertical-align:middle;
line-height:1.3;
padding:0
}

.markdown-body code:before,.markdown-body code:after,.markdown-body tt:before,.markdown-body tt:after{
content:"\\00a0"
}

.markdown-body code{
white-space:nowrap
}

.markdown-body pre>code{
margin:0;
padding:0;
white-space:pre;
border:none;
background:transparent
}

.markdown-body .highlight pre,.markdown-body pre{
background-color:#f8f8f8;
border:1px solid #ddd;
font-size:13px;
line-height:19px;
overflow:auto;
padding:6px 10px;
border-radius:3px
}

.markdown-body pre{
word-wrap:normal
}

.markdown-body pre code,.markdown-body pre tt{
margin:0;
padding:0;
background-color:transparent;
border:none;
word-wrap:normal;
max-width:initial;
display:inline;
overflow:initial;
line-height:inherit
}

.markdown-body pre code:before,.markdown-body pre code:after,.markdown-body pre tt:before,.markdown-body pre tt:after{
content:normal
}


pre .hll { background-color: #ffffcc }
pre .c { color: #999988; font-style: italic } /* Comment */
pre .err { color: #a61717; background-color: #e3d2d2 } /* Error */
pre .k { color: #000000; font-weight: bold } /* Keyword */
pre .o { color: #000000; font-weight: bold } /* Operator */
pre .cm { color: #999988; font-style: italic } /* Comment.Multiline */
pre .cp { color: #999999; font-weight: bold; font-style: italic } /* Comment.Preproc */
pre .c1 { color: #999988; font-style: italic } /* Comment.Single */
pre .cs { color: #999999; font-weight: bold; font-style: italic } /* Comment.Special */
pre .gd { color: #000000; background-color: #ffdddd } /* Generic.Deleted */
pre .ge { color: #000000; font-style: italic } /* Generic.Emph */
pre .gr { color: #aa0000 } /* Generic.Error */
pre .gh { color: #999999 } /* Generic.Heading */
pre .gi { color: #000000; background-color: #ddffdd } /* Generic.Inserted */
pre .go { color: #888888 } /* Generic.Output */
pre .gp { color: #555555 } /* Generic.Prompt */
pre .gs { font-weight: bold } /* Generic.Strong */
pre .gu { color: #aaaaaa } /* Generic.Subheading */
pre .gt { color: #aa0000 } /* Generic.Traceback */
pre .kc { color: #000000; font-weight: bold } /* Keyword.Constant */
pre .kd { color: #000000; font-weight: bold } /* Keyword.Declaration */
pre .kn { color: #000000; font-weight: bold } /* Keyword.Namespace */
pre .kp { color: #000000; font-weight: bold } /* Keyword.Pseudo */
pre .kr { color: #000000; font-weight: bold } /* Keyword.Reserved */
pre .kt { color: #445588; font-weight: bold } /* Keyword.Type */
pre .m { color: #009999 } /* Literal.Number */
pre .s { color: #d01040 } /* Literal.String */
pre .na { color: #008080 } /* Name.Attribute */
pre .nb { color: #0086B3 } /* Name.Builtin */
pre .nc { color: #445588; font-weight: bold } /* Name.Class */
pre .no { color: #008080 } /* Name.Constant */
pre .nd { color: #3c5d5d; font-weight: bold } /* Name.Decorator */
pre .ni { color: #800080 } /* Name.Entity */
pre .ne { color: #990000; font-weight: bold } /* Name.Exception */
pre .nf { color: #990000; font-weight: bold } /* Name.Function */
pre .nl { color: #990000; font-weight: bold } /* Name.Label */
pre .nn { color: #555555 } /* Name.Namespace */
pre .nt { color: #000080 } /* Name.Tag */
pre .nv { color: #008080 } /* Name.Variable */
pre .ow { color: #000000; font-weight: bold } /* Operator.Word */
pre .w { color: #bbbbbb } /* Text.Whitespace */
pre .mf { color: #009999 } /* Literal.Number.Float */
pre .mh { color: #009999 } /* Literal.Number.Hex */
pre .mi { color: #009999 } /* Literal.Number.Integer */
pre .mo { color: #009999 } /* Literal.Number.Oct */
pre .sb { color: #d01040 } /* Literal.String.Backtick */
pre .sc { color: #d01040 } /* Literal.String.Char */
pre .sd { color: #d01040 } /* Literal.String.Doc */
pre .s2 { color: #d01040 } /* Literal.String.Double */
pre .se { color: #d01040 } /* Literal.String.Escape */
pre .sh { color: #d01040 } /* Literal.String.Heredoc */
pre .si { color: #d01040 } /* Literal.String.Interpol */
pre .sx { color: #d01040 } /* Literal.String.Other */
pre .sr { color: #009926 } /* Literal.String.Regex */
pre .s1 { color: #d01040 } /* Literal.String.Single */
pre .ss { color: #990073 } /* Literal.String.Symbol */
pre .bp { color: #999999 } /* Name.Builtin.Pseudo */
pre .vc { color: #008080 } /* Name.Variable.Class */
pre .vg { color: #008080 } /* Name.Variable.Global */
pre .vi { color: #008080 } /* Name.Variable.Instance */
pre .il { color: #009999 } /* Literal.Number.Integer.Long */
"""

class EditorRequestHandler(SimpleHTTPRequestHandler):
    
    def get_html_content(self):
        return HTML_TEMPLATE % {
            'html_head':self.server._document.html_head,
            'in_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._document.in_actions]),
            'out_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._document.out_actions]),
            'markdown_input':self.server._document.text,
            'html_result':self.server._document.getHtml(),
            'mail_style':DOC_STYLE
            }

    def get_html_message(self, *message):
        return '<html><body>%s</body></html>' % '<br />'.join(message)

    def get_html_error(self, message):
        tb = traceback.format_exc()
        print tb
        return '<html><body>%s<br /><pre>%s</pre><a href="/">Continue editing</a></body></html>' % (message, tb)

    def do_GET(self):
        self.send_response(200)
        
        self.send_header("Content-type", "text/html")
        content = self.get_html_content().encode('utf-8')

        self.send_header("Content-length", len(content))
        self.end_headers()
        
        self.wfile.write(content)

    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        
        if self.path == '/ajaxUpdate':
            markdown_message = self.rfile.read(length).decode('utf-8')
            self.server._document.text = markdown_message
            self.wfile.write(self.server._document.getHtml().encode('utf-8'))
            return

        qs = urllib2.urlparse.parse_qs(self.rfile.read(length))
        markdown_input = qs.get('markdown_text')[0].decode('utf-8')
        action = qs.get('SubmitAction')[0]
        self.server._document.text = markdown_input
        self.server._document.form_data = qs
        print('action: '+action)
        
        action_handler = dict(self.server._document.in_actions).get(action) or dict(self.server._document.out_actions).get(action)

        if action_handler:
            content, keep_running = action_handler(self.server._document)
            if content:
                content = content.encode('utf-8')
                self.send_response(200)
                self.send_header("Content-type", "text/html")
            else:
                content = ''
                self.send_response(302)
                self.send_header('Location', '/')
                self.server._running = keep_running
        else:
            content = self.get_html_message('Unknown action: '+action).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content)

class Document:
    
    def __init__(self, markdown_instance, markdown_input, in_actions=None, out_actions=None, custom_html_head='' ,**options):
        self.options = options
        self.md = markdown_instance
        self.text = markdown_input
        self.in_actions = in_actions
        self.out_actions =out_actions
        self.html_head = custom_html_head
        self.form_data = {}
    
    def getHtml(self):
        return self.md.convert(self.text)

    def getHtmlPage(self):
        return OUTPUT_HTML_ENVELOPE % (DOC_STYLE, self.getHtml())

def read_input(input, encoding=None):
    encoding = encoding or "utf-8"
    # Read the source
    if input:
        if isinstance(input, str):
            if not os.path.exists(input):
                with open(input, mode='w'):
                    pass
            input_file = codecs.open(input, mode="r", encoding=encoding)
        else:
            input_file = codecs.getreader(encoding)(input)
        text = input_file.read()
        input_file.close()
    else:
        text = sys.stdin.read()
        if not isinstance(text, unicode):
            text = text.decode(encoding)

    text = text.lstrip('\ufeff') # remove the byte-order mark
    return text

def write_output(output, text, encoding=None):
    encoding = encoding or "utf-8"
    # Write to file or stdout
    if output:
        if isinstance(output, str):
            output_file = codecs.open(output, "w",
                                      encoding=encoding,
                                      errors="xmlcharrefreplace")
            output_file.write(text)
            output_file.close()
        else:
            writer = codecs.getwriter(encoding)
            output_file = writer(output, errors="xmlcharrefreplace")
            output_file.write(text)
            # Don't close here. User may want to write more.
    else:
        sys.stdout.write(text)

def web_action_close(document):
    result = ''
    return result, False

def web_action_preview(document):
    result = document.getHtmlPage()
    return result, True

def web_action_save(document):
    input = document.options.get('input')
    output = document.options.get('output')
    result = document.getHtmlPage()

    # Save files if defined
    if output is not sys.stdout : write_output(output, result)
    if input: write_output(input, document.text)
    return None, True

def web_edit(in_actions=(('Preview',web_action_preview), ('Save',web_action_save), ('Close',web_action_close)), out_actions=(), custom_html_head='', input_text='', **options):
    
    if not options.get('extensions'):
        options.setdefault('extensions',[])

    options.get('extensions').extend(('codehilite','extra'))

    input = options.get('input', None)
    output = options.get('output', None)
    markdown_instance = markdown.Markdown(**options)
    input_text = input and read_input(input) or input_text
    doc = Document(markdown_instance, input_text, in_actions, out_actions, custom_html_head=custom_html_head, **options) 
   
    PORT = 8000
    httpd = HTTPServer(("", PORT), EditorRequestHandler)
    
    print('Opening a browser page on : http://localhost:'+str(PORT))
    webbrowser.open('http://localhost:' + str(PORT))

    httpd._running = True
    httpd._document = doc
    while httpd._running:
        httpd.handle_request()

def parse_options():
    """
    Define and parse `optparse` options for command-line usage.
    """
    usage = """%prog [options] [INPUTFILE]"""
    desc = "Local web editor for Python Markdown, " \
           "a Python implementation of John Gruber's Markdown. " \
           "http://www.freewisdom.org/projects/python-markdown/"
    ver = "%%prog %s" % markdown.version

    parser = optparse.OptionParser(usage=usage, description=desc, version=ver)
    parser.add_option("-f", "--file", dest="filename", default=sys.stdout,
                      help="Write output to OUTPUT_FILE.",
                      metavar="OUTPUT_FILE")
    parser.add_option("-e", "--encoding", dest="encoding",
                      help="Encoding for input and output files.",)
    parser.add_option("-q", "--quiet", default = CRITICAL,
                      action="store_const", const=CRITICAL+10, dest="verbose",
                      help="Suppress all warnings.")
    parser.add_option("-v", "--verbose",
                      action="store_const", const=INFO, dest="verbose",
                      help="Print all warnings.")
    parser.add_option("-s", "--safe", dest="safe", default=False,
                      metavar="SAFE_MODE",
                      help="'replace', 'remove' or 'escape' HTML tags in input")
    parser.add_option("-o", "--output_format", dest="output_format",
                      default='xhtml1', metavar="OUTPUT_FORMAT",
                      help="'xhtml1' (default), 'html4' or 'html5'.")
    parser.add_option("--noisy",
                      action="store_const", const=DEBUG, dest="verbose",
                      help="Print debug messages.")
    parser.add_option("-x", "--extension", action="append", dest="extensions",
                      help = "Load extension EXTENSION (codehilite & extra already included)", metavar="EXTENSION")
    parser.add_option("-n", "--no_lazy_ol", dest="lazy_ol",
                      action='store_false', default=True,
                      help="Observe number of first item of ordered lists.")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        input_file = None
    else:
        input_file = args[0]

    if not options.extensions:
        options.extensions = []

    return {'input': input_file,
            'output': options.filename,
            'safe_mode': options.safe,
            'extensions': options.extensions,
            'encoding': options.encoding,
            'output_format': options.output_format,
            'lazy_ol': options.lazy_ol}, options.verbose

if __name__ == '__main__':
    """Run Markdown from the command line."""

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options: sys.exit(2)
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())

    # Run
    web_edit(**options)

