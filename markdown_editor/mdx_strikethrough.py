#!/usr/bin/env python
# -*- coding: utf-8 -*-

import markdown

DEL_RE = r'(~~)(.*?)~~' # github strikethrough

class StrikeThroughExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # Create the del pattern
        del_tag = markdown.inlinepatterns.SimpleTagPattern(DEL_RE, 'del')
        # Insert del pattern into markdown parser
        md.inlinePatterns.add('del', del_tag, '>not_strong')

def makeExtension(configs={}):
    return StrikeThroughExtension(configs=configs)

