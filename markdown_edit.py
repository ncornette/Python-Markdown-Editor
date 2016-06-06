#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import logging
import optparse
import sys
from logging import DEBUG, INFO, CRITICAL

import markdown

from markdown_editor.editor import MarkdownDocument, MARKDOWN_EXT

logger = logging.getLogger('MARKDOWN_EDITOR')


def parse_options():  # pragma: no cover
    """
    Define and parse `optparse` options for command-line usage.
    """
    usage = """%prog [options] [INPUTFILE]"""
    desc = "Local web editor for Python Markdown, " \
           "a Python implementation of John Gruber's Markdown. " \
           "http://www.freewisdom.org/projects/python-markdown/"
    ver = '%prog {}'.format(markdown.version)

    parser = optparse.OptionParser(usage=usage, description=desc, version=ver)
    parser.add_option("-p", "--port", dest="port", default=8222,
                      help="Change listen port for Web eidt.")
    parser.add_option("-t", "--terminal", dest="term_edit",
                      action='store_true', default=False,
                      help="Edit within terminal.")
    parser.add_option("-w", "--preview", dest="term_preview",
                      action='store_true', default=False,
                      help="Preview in webbrowser.")
    parser.add_option("-f", "--file", dest="filename", default=None,
                      help="Write output to OUTPUT_FILE.",
                      metavar="OUTPUT_FILE")
    parser.add_option("-e", "--encoding", dest="encoding",
                      help="Encoding for input and output files.", )
    parser.add_option("-q", "--quiet", default=CRITICAL,
                      action="store_const", const=CRITICAL + 10, dest="verbose",
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
                      help="Load extension EXTENSION (codehilite & extra already included)",
                      metavar="EXTENSION")
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
            'term_edit': options.term_edit or options.term_preview,
            'term_action': options.term_preview and 'p' or 'e',
            'port': options.port,
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
    markdown_document = MarkdownDocument(infile=options['input'], outfile=options['output'],
                                         md=markdown_processor)
    # Run
    if term_edit:
        from markdown_editor import terminal_edit
        terminal_edit.start(markdown_document, default_action=options['term_action'])
    else:
        from markdown_editor import web_edit
        web_edit.start(markdown_document, port=options['port'])

if __name__ == '__main__':
    main()
