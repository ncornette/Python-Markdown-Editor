Python-Markdown-Editor
======================

|Build Status| |PyPI py versions| |PyPI version|

Standalone editor for your local markdown files

Installation
~~~~~~~~~~~~

To install the latest stable version from Pypi :

.. code:: sh

    $ pip install markdown-editor

Usage
~~~~~

.. code:: sh

    $ markdown_edit README.md

It will open the editor in your browser :

.. figure:: https://github.com/ncornette/Python-Markdown-Editor/raw/master/screenshot.png
   :alt: screenshot

   screenshot

Features
~~~~~~~~

-  Side-by-side markdown editor & html preview
-  Live, when you type html preview
-  Codehilite & markdown extra syntax support by default
-  Github syntax support
-  Github styles for rendering and codehilite
-  Scrollbars sync

Dependencies
~~~~~~~~~~~~

-  markdown
-  pygments

Other usage examples
~~~~~~~~~~~~~~~~~~~~

Launch editor without input file for testing :

.. code:: bash

    $ markdown_edit 

Edit markdown file and save both markdown and html outputs :

.. code:: bash

    $ markdown_edit -f README.html README.md

Extensible
~~~~~~~~~~

You can import this script as a module to write your own applications
based on the markdown editor.

example :

.. code:: python

    import markdown_edit

    # ...

    def action_send(document):

        send_markdown_text(document.text)
        # or 
        send_raw_html_code(document.getHtml())
        # or 
        send_html_with_styles(document.getHtmlPage())

        return html_to_display_as_result, keep_running_local_server

    if __name__ == '__main__:
        markdown_edit.web_edit(
            actions =
                [
                    ('Send',action_send),
                ],
            title = MY_HTML_HEAD)

.. |Build Status| image:: https://travis-ci.org/ncornette/Python-Markdown-Editor.svg?branch=master
   :target: https://travis-ci.org/ncornette/Python-Markdown-Editor
.. |PyPI py versions| image:: https://img.shields.io/pypi/pyversions/Markdown-Editor.svg?maxAge=2592000
   :target: https://pypi.python.org/pypi/Markdown-Editor
.. |PyPI version| image:: https://img.shields.io/pypi/v/Markdown-Editor.svg?maxAge=2592000
   :target: https://pypi.python.org/pypi/Markdown-Editor
