#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import webbrowser

import sys
from bottle import run, template, static_file, Bottle, request, redirect, response
from markdown_editor.editor import Action, _as_objects, MarkdownDocument

script_dir = os.path.dirname(os.path.realpath(__file__))

PAGE_HEADER_TEMPLATE = u'&nbsp;<span class="glyphicon glyphicon-file"></span>&nbsp;<span>{}</span>'

ACTION_TEMPLATE = u"""\
<input type="submit" class="btn btn-default" name="SubmitAction" value="{}"\
onclick="$('#pleaseWaitDialog').modal('show')">"""

SAVE_ACTION_TEMPLATE = u"""\
<input type="button" class="btn btn-default" value="{}" onclick="ajaxSaveFile();">"""


class WebAction(Action):
    def __init__(self, name, function, key=None, action_template=ACTION_TEMPLATE):
        Action.__init__(self, name, function, key)
        self.html = action_template.format(name)


app = Bottle()


def action_close(_):
    return "Server Stopped", False


def action_preview(_):
    return None, '/preview'


def handle_form_action(action):
    content, location = action(app.config['myapp.document'])
    if content and location:
        return content
    elif location is True:
        redirect('/')
    elif location:
        redirect(location)
    else:
        sys.stderr.close()
        return content


def read_unicode(stream):
    return codecs.getreader('utf8')(stream).read()


@app.post('/ajax/save')
def ajax_save():
    doc = app.config['myapp.document']
    doc.text = read_unicode(request.body)
    doc.save()


@app.post('/ajax/preview')
def ajax_preview():
    doc = app.config['myapp.document']
    doc.text = read_unicode(request.body)
    return doc.get_html()


@app.post('/ajax/vim_mode')
def ajax_vim_mode():
    response.set_cookie('vim_mode', 'true' if request.json.get('vim_mode') else 'false')


@app.post('/ajax/<path>')
def ajax_handle(path):
    handler = app.config['myapp.ajax_handlers.' + path]
    return handler(app.config['myapp.document'], read_unicode(request.body))


@app.get('/libs/<path:path>')
def static_lib(path):
    return static_file(path, os.path.join(script_dir, 'libs'))


@app.get('/css/<path:path>')
def static_css(path):
    return static_file(path, os.path.join(script_dir, 'css'))


@app.get('/js/<path:path>')
def static_css(path):
    return static_file(path, os.path.join(script_dir, 'js'))


@app.post('/')
def submit_action():
    action = request.forms.SubmitAction
    for a in app.config['myapp.in_actions'] + app.config['myapp.out_actions']:
        if a.name == action:
            return handle_form_action(a)
    raise AttributeError('Unknown action: ' + action)


@app.get('/preview')
def preview():
    return app.config['myapp.document'].get_html_page()


@app.get('/')
def editor():
    vim_mode = request.get_cookie('vim_mode', 'false')

    return template(os.path.join(script_dir, 'markdown_edit'),
                    html_head=app.config['myapp.html_head'],
                    in_actions=u'&nbsp;'.join([a.html for a in app.config['myapp.in_actions']]),
                    out_actions=u'&nbsp;'.join([a.html for a in app.config['myapp.out_actions']]),
                    markdown_input=app.config['myapp.document'].text,
                    vim_mode='checked' if vim_mode == 'true' else '')


def start(doc, custom_actions=None, title='', ajax_handlers=None, port=8222):

    default_actions = [WebAction('Preview', action_preview), WebAction('Close', action_close)]

    if doc.input_file or doc.output_file:
        default_actions.insert(0, WebAction('Save', ajax_save, action_template=SAVE_ACTION_TEMPLATE))

    if title:
        html_head = title
    elif doc.input_file or doc.output_file:
        html_head = PAGE_HEADER_TEMPLATE.format(os.path.basename(doc.input_file or doc.output_file))
    else:
        html_head = ''

    app.config.load_dict({
        'autojson': False,
        'myapp': {
            'document': doc,
            'in_actions': default_actions,
            'out_actions': _as_objects(custom_actions, WebAction),
            'html_head': html_head,
            'ajax_handlers': ajax_handlers or {}
            }
        }, make_namespaces=True)

    webbrowser.open('http://localhost:{}'.format(port))

    run(app, host='localhost', port=port, debug=False, reloader=False)

if __name__ == '__main__':
    start(MarkdownDocument())
