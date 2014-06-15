#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os.path import join

if sys.version_info[0]<3:
    import SimpleHTTPServer
    import SocketServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SimpleHTTPServer import BaseHTTPServer
    from BaseHTTPServer import HTTPServer
    import urllib2
    parse_qsl = urllib2.urlparse.parse_qsl
else:
    import http.server
    import socketserver
    import urllib.request, urllib.error, urllib.parse
    from http.server import SimpleHTTPRequestHandler
    from http.server import HTTPServer
    from urllib.parse import parse_qsl

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

sys.path.append(scriptdir)
MARKDOWN_EXT = ('codehilite','extra','strikethrough')
MARKDOWN_CSS = join(scriptdir, 'styles/markdown.css')
PYGMENTS_CSS = join(scriptdir, 'styles/pygments.css')
ACTION_TEMPLATE = """<input type="submit" class="btn btn-default" name="SubmitAction" value="%s" onclick="$('#pleaseWaitDialog').modal('show')">"""
BOTTOM_PADDING = '<br />' * 2

class EditorRequestHandler(SimpleHTTPRequestHandler):
    
    def get_html_content(self):
        with open(join(scriptdir,'markdown_edit.html')) as template:
            return template.read() % {
                'html_head':callable(self.server._html_head) and self.server._html_head() or self.server._html_head,
                'in_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._in_actions]),
                'out_actions':'&nbsp;'.join([ACTION_TEMPLATE % k for k,v in self.server._out_actions]),
                'markdown_input':self.server._document.text,
                'html_result':self.server._document.getHtml() + BOTTOM_PADDING,
                'mail_style':self.server._document.inline_css
                }

    def do_GET(self):
        if self.path.startswith('/libs'):
            lib_path = join(scriptdir, self.path[1:])
            print(lib_path)
            with open(lib_path, 'rb') as lib:
                content = lib.read()
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(self.path)[0])
        elif self.path == '/':
            content = self.get_html_content().encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
        else:
            content = ''
            self.send_response(404)
    
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        
        # Ajax update preview
        if self.path == '/ajaxUpdate':
            markdown_message = self.rfile.read(length).decode('utf-8')
            self.server._document.text = markdown_message
            self.wfile.write(self.server._document.getHtml().encode('utf-8') + BOTTOM_PADDING.encode('utf-8'))
            return

        # Ajax action handler
        if self.path in self.server._ajax_handlers:
            request_data = self.rfile.read(length).decode('utf-8')
            handler_func = self.server._ajax_handlers.get(self.path)
            result_data = handler_func(self.server._document, request_data)
            self.wfile.write(result_data.encode('utf-8'))
            return
            
        # Form submit action
        form_data = self.rfile.read(length)
        qs = dict(parse_qsl(codecs.decode(form_data,'utf-8'), True))
        markdown_input = qs['markdown_text']
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
                print(tb)
                footer = '<a href="/">Continue editing</a>'
                content = '<html><body><h4>%s</h4><pre>%s</pre>\n%s</body></html>' % (e.message, tb, footer)
                keep_running = True

            if content:
                content = codecs.encode(content,'utf-8')
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.server._running = keep_running
            else:
                content = codecs.encode('','utf-8')
                self.send_response(302)
                self.send_header('Location', '/')
                self.server._running = keep_running
        else:
            content = codecs.encode('','utf-8')
            self.send_response(302)
            self.send_header('Location', '/')
            
        self.send_header("Content-length", len(content))
        self.end_headers()
        self.wfile.write(content)

class MarkdownDocument:
    
    def __init__(self, mdtext='', infile=None, outfile=None, md=None, markdown_css=MARKDOWN_CSS, pygments_css=PYGMENTS_CSS ):
        self.input_file = infile
        self.output_file = outfile
        initial_markdown = mdtext and mdtext or read_input(self.input_file)
        self.inline_css = ''

        if markdown_css:
            with open(markdown_css) as markdown_css_file:
                self.inline_css += markdown_css_file.read()

        if pygments_css:
            with open(pygments_css) as pygments_css_file:
                self.inline_css += pygments_css_file.read()
        
        if not md:
            self.md = markdown.Markdown(extensions=MARKDOWN_EXT)
        else:
            self.md = md

        self.text = initial_markdown
        self.form_data = {} # used by clients to handle custom form actions
    
    def getHtml(self):
        return self.md.convert(self.text)

    def getHtmlPage(self):
        return """<!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
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
        """ % (self.inline_css, self.getHtml())

def read_input(input_file, encoding=None):
    encoding = encoding or "utf-8"
    text = ''
    # Read the source
    if input_file == '-':
        text = sys.stdin.read()
        if not isinstance(text, str):
            text = text.decode(encoding)
    elif input_file:
        if isinstance(input_file, str):
            if not os.path.exists(input_file):
                with open(input_file, mode='w'):
                    pass
            input_file = codecs.open(input_file, mode="rb", encoding=encoding)
        else:
            input_file = codecs.getreader(encoding)(input_file)
        text = input_file.read()
        input_file.close()

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
    input_file = document.input_file
    output_file = document.output_file
    result = document.getHtmlPage()

    # Save files if defined
    if output_file: write_output(output_file, result)
    if input_file: write_output(input_file, document.text)
    return None, True

def sys_edit(markdown_document, editor=None):
    use_editor = editor or SYS_EDITOR
    with tempfile.NamedTemporaryFile(mode='r+',suffix=".markdown") as temp:
        temp.write(markdown_document.text.encode('utf-8'))
        temp.flush()
        call([use_editor, temp.name])
        temp.seek(0)
        markdown_document.text = temp.read().decode('utf-8')
    return markdown_document

def terminal_edit(doc = None, actions=[]):
    all_actions = actions + [('Edit again',None,'e'), ('Preview',None,'p')]

    if not doc:
        doc = MarkdownDocument()

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
            resp = input('''Choose command to continue : 

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
            elif command in action_funcs:
                result, keep_running =  action_funcs[command](doc)

def web_edit(doc = None, actions=[], title='', ajax_handlers={}):
    """
    Launches webbrowser editor
    Params :
        - doc: MarkdownDocument instance to edit
        - actions: list of ('action_name', action_handker) to be displayed as buttons in web interface

            action_handler is a function that receives MarkdownDocument as uniquqe parameter and must return a tuple, example : 

            def action(markdown_document):
                html_result = '<h1>Done</h1>'
                kill_editor = True
                return html_result, kill_editor

        - title: html code to insert above the editor
        - ajax_handlers: map of 'ajax_req_path':ajax_handler_func to handle your own ajax requests
    """

    default_actions = [('Preview',action_preview), ('Close',action_close)]

    if not doc:
        doc = MarkdownDocument()

    if doc.input_file or doc.output_file:
        default_actions.insert(0, ('Save',action_save))

    PORT = 8000
    httpd = HTTPServer(("", PORT), EditorRequestHandler)
    
    print('Opening a browser page on : http://localhost:'+str(PORT))
    webbrowser.open('http://localhost:' + str(PORT))

    httpd._running = True
    httpd._document = doc
    httpd._in_actions = default_actions
    httpd._out_actions = actions
    httpd._html_head = title or doc.input_file and '&nbsp;<span class="glyphicon glyphicon-file"></span>&nbsp;<span>%s</span>' % os.path.basename(doc.input_file) or ''
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
    
    options.extensions.extend(MARKDOWN_EXT)

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
    
    term_edit = options.pop('term_edit')
    markdown_processor = markdown.Markdown(**options)
    markdown_document = MarkdownDocument(infile=options['input'], outfile=options['output'], md=markdown_processor)

    # Run
    if term_edit:
        terminal_edit(markdown_document)
    else:
        web_edit(markdown_document)

if __name__ == '__main__':
    main()

