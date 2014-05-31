Python-Markdown-Editor
======================

Standalone editor for your markdown files

### Features
 - Side-by-side markdown editor & html preview
 - Live, when you type html preview
 - Codehilite & markdown extra syntax support by default
 - Github syntax support 
 - Github styles for rendering and codehilite

![screenshot](https://github.com/ncornette/Python-Markdown-Editor/raw/master/screenshot.png)

### Dependencies
 - Python-Markdown

### Usage

Launch editor for testing :
```bash
$ markdown_edit.py 
```

Edit existing markdown file for preview :
```bash
$ markdown_edit.py readme.md
```

Edit existing markdown file and save html output file :
```bash
$ markdown_edit.py -f readme.html readme.md
```

### Extensible

You can import this script as a module to write your own applications based on the markdown editor.

example : 

```python
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


```
