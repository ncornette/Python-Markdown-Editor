#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import os

import markdown
import codecs

from os.path import join

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.append(script_dir)

MARKDOWN_EXT = ('codehilite', 'extra', 'strikethrough')
MARKDOWN_CSS = join(script_dir, 'css/markdown.css')
PYGMENTS_CSS = join(script_dir, 'css/pygments.css')


def _as_objects(objs_or_tuples, _type):
    return [isinstance(a, (list, tuple)) and _type(*a) or a for a in objs_or_tuples or []]


class Action(object):

    def __init__(self, name, function, key=None):
        """
        :type name: str
        :type function: callable
        :type key: str
        :type template: str
        """
        self.name = name
        self.function = function
        self.key = key

    def __call__(self, document):
        """
        Call the action

        :type document: MarkdownDocument
        :param document:
        :return: - (None, True)      : To continue with editor
                 - ('Ok', True)      : To send 'Ok' as a result page
                 - ('Closed', False) : To send 'Closed' as a result page and stop the server
                 - (None, '/page')   : to redirect to '/page'
        """
        content, next_location = self.function(document)
        return content, next_location


def read_input(input_file, encoding='utf8'):
    text = ''
    # Read the source
    if input_file == '-':
        text = codecs.getreader('utf8')(sys.stdin, errors="xmlcharrefreplace").read()
    elif input_file:
        if isinstance(input_file, str):
            if not os.path.exists(input_file):
                with codecs.open(input_file, mode='w'):
                    pass
            with codecs.open(input_file, 'rb', encoding, errors="xmlcharrefreplace") as f:
                text = f.read()
        else:
            input_file = codecs.getreader(encoding)(input_file, errors="xmlcharrefreplace")
            text = input_file.read()

    text = text.lstrip('\ufeff')  # remove the byte-order mark
    return text


def write_output(output, text, encoding='utf8'):
    # Write to file or stdout
    if output and output != '-':
        if isinstance(output, str):
            with codecs.open(output, "w", encoding=encoding, errors="xmlcharrefreplace") as f:
                f.write(text)
        else:
            writer = codecs.getwriter(encoding)
            output_file = writer(output, errors="xmlcharrefreplace")
            output_file.write(text)
            # Don't close here. User may want to write more.
    else:
        sys.stdout.write(text)


class MarkdownDocument:
    def __init__(self, mdtext='', infile=None, outfile=None, md=None, markdown_css=MARKDOWN_CSS,
                 pygments_css=PYGMENTS_CSS):
        self.input_file = infile
        self.output_file = outfile
        initial_markdown = mdtext and mdtext or read_input(self.input_file)
        self.inline_css = u''
        self.newline_update = None

        if markdown_css:
            with codecs.open(markdown_css, 'r', 'utf8') as markdown_css_file:
                self.inline_css += markdown_css_file.read()

        if pygments_css:
            with codecs.open(pygments_css, 'r', 'utf8') as pygments_css_file:
                self.inline_css += pygments_css_file.read()

        if not md:
            self.md = markdown.Markdown(extensions=MARKDOWN_EXT)
        else:
            self.md = md

        self.text = initial_markdown
        self.form_data = {}  # used by clients to handle custom form actions

    def fix_crlf_input_text(self):
        if self.newline_update and self.newline_update != '\r\n':
            self.text = re.sub('\r\n', self.newline_update, self.text)

    def detect_newline(self):
        new_line_match = re.search('\r\n|\r|\n', self.text)
        if new_line_match:
            self.newline_update = new_line_match.group()
        else:
            self.newline_update = os.linesep
        return self.newline_update

    def save(self):
        self.fix_crlf_input_text()

        if self.output_file:
            write_output(self.output_file, self.get_html_page())

        if self.input_file:
            write_output(self.input_file, self.text)

        return None, True

    def get_html(self):
        return self.md.reset().convert(self.text)

    def get_html_page(self):
        return u"""\
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style type="text/css">
        {}
        </style>
        </head>
        <body>
        <div class="markdown-body">
        {}
        </div>
        </body>
        </html>
        """.format(self.inline_css, self.get_html())
