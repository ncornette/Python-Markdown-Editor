#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
from markdown_editor.editor import MarkdownDocument

class MyTestCase(unittest.TestCase):

    def test_document_html(self):
        self.assertEqual('<h3>Spam</h3>', MarkdownDocument('### Spam').get_html())

    def test_document_html_page(self):
        self.assertIn('<h3>Spam</h3>', MarkdownDocument('### Spam').get_html_page())

    def test_document_html_page_unicode(self):
        self.assertIn('<h3>Spam é</h3>', MarkdownDocument('### Spam é', 'utf-8').get_html_page())

    def test_detect_newline(self):
        self.assertEqual(os.linesep, MarkdownDocument('### Spam').detect_newline())
        self.assertEqual('\n', MarkdownDocument('### Spam\n').detect_newline())
        self.assertEqual('\r\n', MarkdownDocument('### Spam\r\nEggs').detect_newline())
        self.assertEqual('\r', MarkdownDocument('### Spam\rEggs').detect_newline())

if __name__ == '__main__':
    unittest.main()
