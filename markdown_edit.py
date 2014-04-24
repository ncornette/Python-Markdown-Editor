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
import tempfile
from subprocess import call
import mimetypes

scriptdir = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger('MARKDOWN_EDITOR')
SYS_EDITOR = os.environ.get('EDITOR','vim')
MD_EXTENSIONS = ('codehilite','extra')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html id="editor">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Markdown Editor</title>
        <link href="libs/bootstrap-3.1.1-dist/css/bootstrap.css" rel="stylesheet">
        <link href="libs/bootstrap-3.1.1-dist/css/bootstrap-theme.css" rel="stylesheet">
        <link href="libs/codemirror/codemirror.css" rel="stylesheet">
        <link href="libs/codemirror/theme/neat.css" rel="stylesheet">
        <script>
            var myCodeMirror;
            function updateHtmlPreview() {
                $.post( "ajaxUpdate", myCodeMirror.getValue())
                    .done(function( data ) {$("#html_result").html(data)});
            }
            function updateMarkdownInput(value) {
                myCodeMirror.setValue(value)
            }
        </script>
        <style>
            %(mail_style)s
        </style>
        <script src="libs/jquery-1.11.0-dist/jquery-1.11.0.js"></script>
        <script src="libs/bootstrap-3.1.1-dist/js/bootstrap.js"></script>
        <script src="libs/codemirror/codemirror.js"></script>
        <script src="libs/codemirror/mode/markdown.js"></script>
    </head>

    <body style="background-color: rgb(204, 204, 204);">
        <form class="form-horizontal" method="post" action="/" name="markdown_input">
        <div style="position:fixed; top:0; bottom:0; left:0; right:0">
        
        <div style="margin-top:15px; margin-left:15px; margin-right:15px" id="head">%(html_head)s</div>

        <div id="mdedit" style="position: absolute; height:40px; width:100%%; top:0;" class="row">
            <div class="col-sm-6">
                <div style="margin:15px"  class="btn-toolbar"><div class="btn-group btn-group-sm">%(in_actions)s</div></div>
            </div>
            <div style="padding-left:0px" class="col-sm-6">
                <div style="margin:15px" class="btn-toolbar"><div class="btn-group btn-group-sm">%(out_actions)s</div></div>
            </div>
        </div>

        <div id="mdedit-body" style="padding:15px; position: absolute; top:0; bottom:0; left:0; right:0" class="row">
            <div style="height:100%%" class="col-sm-6">
                <textarea style="font-family: monospace; font-size: small; color:#222; width:100%%; height:100%%" class="form-control" onKeyUp="updateHtmlPreview()" id="markdown_input" cols="80" rows="30" name="markdown_text">%(markdown_input)s</textarea>
            </div>
            <div style="height:100%%; padding-left:0px" class="col-sm-6">
                <div class="html-output markdown-body" id="html_result" style="overflow: auto; height:100%%">%(html_result)s</div>
            </div>
        </div>
        </div>
        </form>

        <div class="modal" id="pleaseWaitDialog" data-backdrop="static" data-keyboard="false">
          <div class="modal-dialog ">
            <div id="wait-content" class="modal-content">
                <div class="modal-header">
                    <h1>Processing...</h1>
                </div>
                <div class="modal-body">
                    <div class="progress progress-striped active">
                        <div class="progress-bar" style="width: 100%%;"></div>
                    </div>
                </div>
            </div>
          </div>
        </div>

    </body>
    <script>
        
        // Setup custom header height
        head_height = $('#head').outerHeight(true)
        $('#mdedit').css('top', head_height+'px')
        $('#mdedit-body').css('top', (head_height+$('#mdedit').height())+'px')

        // Setup CodeMirror for markdown input
        myCodeMirror = CodeMirror.fromTextArea($('#markdown_input')[0], {
            "value": "",
            "mode":  {name:"markdown",fencedCodeBlocks:true, underscoresBreakWords:false},
            "indentUnit": "4",
            "theme":  "neat"
            });
        $(".CodeMirror").addClass("form-control")
        $(".CodeMirror").addClass("focusedInput")
        myCodeMirror.setSize("100%%","100%%")
        myCodeMirror.on("keyup", updateHtmlPreview)

        // Setup scrollbars sync
        var s1 = myCodeMirror.display.scrollbarV
        var s2 = $('#html_result')[0]

        function select_scroll(e) {
            viewHeight = s2.getBoundingClientRect().height
            ratio = (s2.scrollHeight-viewHeight)/(s1.scrollHeight-viewHeight)
            s2.scrollTop = s1.scrollTop*ratio;
        }

        s1.addEventListener('scroll', select_scroll, false);

        // Set Focus on markdown input
        $('#pleaseWaitDialog').on('hidden.bs.modal', function () {myCodeMirror.focus()})
        myCodeMirror.focus()
        
    </script>

</html>
"""

ACTION_TEMPLATE = """<input type="submit" class="btn btn-default" name="SubmitAction" value="%s" onclick="$('#pleaseWaitDialog').modal('show')">"""

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

.focusedInput {
border-color: #ccc;
border-color: rgba(82,168,236,.8);
outline: 0;
outline: thin dotted \9;
-moz-box-shadow: 0 0 8px rgba(82,168,236,.6);
box-shadow: 0 0 8px rgba(82,168,236,.6);
}

.html-output {
margin-left: 0;
margin-right: 0;
background-color: #fff;
border-width: 1px;
border-color: #ddd;
border-radius: 4px;
box-shadow: none;
position: relative;
padding: 15px 15px 0px;
height:100%;
}

#editor {
overflow: hidden;
}

body {
background-color: #FFFFFF;
overflow:auto;
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

BOTTOM_PADDING = '<br />' * 2

class EditorRequestHandler(SimpleHTTPRequestHandler):
    
    def get_html_content(self):
        return HTML_TEMPLATE % {
            'html_head':callable(self.server._html_head) and self.server._html_head() or self.server._html_head,
            'in_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._in_actions]),
            'out_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._out_actions]),
            'markdown_input':self.server._document.text,
            'html_result':self.server._document.getHtml() + BOTTOM_PADDING,
            'mail_style':DOC_STYLE
            }

    def do_GET(self):
        if self.path.startswith('/libs'):
            lib_path = os.path.join(scriptdir, self.path[1:])
            print lib_path
            with open(lib_path, 'r') as lib:
                content = lib.read()
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(self.path)[0])
        elif self.path != '/':
            content = ''
            self.send_response(404)
        else:
            content = self.get_html_content().encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
    
        self.send_header("Content-length", len(content))
        
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        
        if self.server._ajax_handlers.has_key(self.path):
            request_data = self.rfile.read(length).decode('utf-8')
            result_data = self.server._ajax_handlers.get(self.path)(self.server._document, request_data)
            self.wfile.write(result_data.encode('utf-8'))
            return
            
        if self.path == '/ajaxUpdate':
            markdown_message = self.rfile.read(length).decode('utf-8')
            self.server._document.text = markdown_message
            self.wfile.write(self.server._document.getHtml().encode('utf-8') + BOTTOM_PADDING)
            return

        qs = dict(urllib2.urlparse.parse_qsl(self.rfile.read(length), True))
        markdown_input = qs['markdown_text'].decode('utf-8')
        action = qs.get('SubmitAction','')
        self.server._document.text = markdown_input
        self.server._document.form_data = qs
        print('action: '+action)
        
        action_handler = dict(self.server._in_actions).get(action) or dict(self.server._out_actions).get(action)

        if action_handler:
            try:
                content, keep_running = action_handler(self.server._document)
            except Exception as e:
                tb = traceback.format_exc()
                print tb
                footer = '<a href="/">Continue editing</a>'
                content = '<html><body><h4>%s</h4><pre>%s</pre>\n%s</body></html>' % (e.message, tb, footer)
                keep_running = True

            if content:
                content = content.encode('utf-8')
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.server._running = keep_running
            else:
                content = ''
                self.send_response(302)
                self.send_header('Location', '/')
                self.server._running = keep_running
        else:
            content = ''
            self.send_response(302)
            self.send_header('Location', '/')
            
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content)

class MarkdownDocument:
    
    def __init__(self, mdtext='', infile=None, outfile=None, md=markdown.Markdown(extensions=MD_EXTENSIONS) ):
        self.input_file = infile
        self.output_file = outfile
        initial_markdown = self.input_file and read_input(self.input_file) or mdtext

        self.md = md
        self.text = initial_markdown
        self.form_data = {} # used by clients to handle custom form actions
    
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

def action_close(document):
    return None, False

def action_preview(document):
    result = document.getHtmlPage()
    return result, True

def action_save(document):
    input = document.input_file
    output = document.output_file
    result = document.getHtmlPage()

    # Save files if defined
    if output: write_output(output, result)
    if input: write_output(input, document.text)
    return None, True

def sys_edit(document, editor=None):
    use_editor = editor or SYS_EDITOR
    with tempfile.NamedTemporaryFile(mode='r+',suffix=".markdown") as temp:
        temp.write(document.text.encode('utf-8'))
        temp.flush()
        call([use_editor, temp.name])
        temp.seek(0)
        document.text = temp.read().decode('utf-8')
    return document

def terminal_edit(doc = MarkdownDocument(), custom_actions=[]):
    all_actions = custom_actions + [('Edit again',None,'e'), ('Preview',None,'p')]

    if doc.input_file or doc.output_file:
        all_actions.append(('Save',action_save,'s'))
    all_actions.append(('Quit',action_close,'q'))

    action_funcs  = dict([(a[2], a[1]) for a in all_actions])
    actions_prompt = [a[2]+' : '+a[0] for a in all_actions]

    keep_running = True
    with tempfile.NamedTemporaryFile(mode='r+',suffix=".html") as temp:
        temp.write(sys_edit(doc).getHtmlPage().encode('utf-8'))
        temp.flush()
        while keep_running:
            resp = raw_input('''Choose command to continue : 

%s
?: ''' % ('\n'.join(actions_prompt))
            )
            
            command = resp and resp[0] or ''
            if command == 'e':
                temp.seek(0)
                temp.write(sys_edit(doc).getHtmlPage().encode('utf-8'))
                temp.truncate()
                temp.flush()
            elif command == 'p':
                webbrowser.open(temp.name)
            elif action_funcs.has_key(command):
                result, keep_running =  action_funcs[command](doc)

def web_edit(doc = MarkdownDocument(), custom_actions=[], custom_html_head='', ajax_handlers={}):
    """
    Launches webbrowser editor
    Params :
        - doc: MarkdownDocument instance to edit
        - custom_action: list of ('action_name', action_handker) to be displayed as buttons in web interface

            action_handler is a function that receives MarkdownDocument as uniquqe parameter and must return a tuple, example : 

            def action(markdown_document):
                html_result = '<h1>Done</h1>'
                kill_editor = True
                return html_result, kill_editor

        - custom_html_head: html code to insert above the editor
        - ajax_handlers: map of 'ajax_req_path':ajax_handler_func to handle your own ajax requests
    """

    actions = [('Preview',action_preview), ('Close',action_close)]

    if doc.input_file or doc.output_file:
        actions.insert(0, ('Save',action_save))

    PORT = 8000
    httpd = HTTPServer(("", PORT), EditorRequestHandler)
    
    print('Opening a browser page on : http://localhost:'+str(PORT))
    webbrowser.open('http://localhost:' + str(PORT))

    httpd._running = True
    httpd._document = doc
    httpd._in_actions = actions
    httpd._out_actions = custom_actions
    httpd._html_head = custom_html_head or doc.input_file and '&nbsp;<span class="glyphicon glyphicon-file"></span>&nbsp;<span>%s</span>' % os.path.basename(doc.input_file) or ''
    httpd._ajax_handlers = ajax_handlers
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
    parser.add_option("-t", "--terminal", dest="term_edit",
                      action='store_true', default=False,
                      help="Edit within terminal.")
    parser.add_option("-f", "--file", dest="filename", default=None,
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
    
    options.extensions.extend(MD_EXTENSIONS)

    return {'input': input_file,
            'term_edit':options.term_edit,
            'output': options.filename,
            'safe_mode': options.safe,
            'extensions': options.extensions,
            'encoding': options.encoding,
            'output_format': options.output_format,
            'lazy_ol': options.lazy_ol}, options.verbose

def main():
    """Run Markdown from the command line."""

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options: sys.exit(2)
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())
    
    markdown_processor = markdown.Markdown(**options)
    markdown_document = MarkdownDocument(infile=options['input'], outfile=options['output'], md=markdown_processor)

    # Run
    if options.get('term_edit'):
        terminal_edit(markdown_document)
    else:
        web_edit(markdown_document)

if __name__ == '__main__':
    main()

