#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os
import tempfile

import sys
import webbrowser

from subprocess import call

from markdown_editor.editor import Action, MarkdownDocument, _as_objects
from markdown_editor.web_edit import action_close

SYS_EDITOR = os.environ.get('EDITOR', 'vim')

if sys.version_info[0] >= 3:
    raw_input = input


def sys_edit(markdown_document, editor=None):
    with tempfile.NamedTemporaryFile(mode='r+', suffix=".markdown") as f:
        temp = codecs.getwriter('utf8')(f) if (sys.version_info[0] < 3) else f
        temp.write(markdown_document.text)
        temp.flush()
        call([editor or SYS_EDITOR, temp.name])
        with codecs.open(temp.name, 'r', 'utf8') as g:
            markdown_document.text = g.read()
    return markdown_document


def start(doc, actions=[], default_action=None):
    all_actions = _as_objects(actions, Action) + [Action('Edit again', None, 'e'), Action('Preview', None, 'p')]

    if doc.input_file or doc.output_file:
        all_actions.append(Action('Save', MarkdownDocument.save, 's'))
    all_actions.append(Action('Quit', action_close, 'q'))

    action_funcs = dict([(a.key, a) for a in all_actions])
    actions_prompt = [a.key + ' : ' + a.name for a in all_actions]

    keep_running = True
    with tempfile.NamedTemporaryFile(mode='r+', suffix=".html") as f:
        temp = codecs.getwriter('utf8')(f) if sys.version_info[0] < 3 else f
        temp.write(doc.get_html_page())
        temp.flush()
        while keep_running:
            command = default_action or raw_input('''Choose command :\n\n{}\n?: '''.format(
                    '\n'.join(actions_prompt)))

            default_action = None
            if command[:1] == 'e':
                temp.seek(0)
                temp.write(sys_edit(doc).get_html_page())
                temp.truncate()
                temp.flush()
            elif command[:1] == 'p':
                webbrowser.open('file:///{}'.format(temp.name))
            elif command[:1] in action_funcs:
                result, keep_running = action_funcs[command](doc)

if __name__ == '__main__':
    start(MarkdownDocument())