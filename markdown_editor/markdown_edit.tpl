<!DOCTYPE html>
<html id="editor">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Markdown Editor</title>
        <link href="/libs/bootstrap-3.1.1-dist/css/bootstrap.css" rel="stylesheet">
        <link href="/libs/bootstrap-3.1.1-dist/css/bootstrap-theme.css" rel="stylesheet">
        <link href="/libs/codemirror-5.15.2/codemirror.css" rel="stylesheet">
        <link href="/libs/codemirror-5.15.2/theme/neat.css" rel="stylesheet">
        <link href="/libs/codemirror-5.15.2/theme/3024-night.css" rel="stylesheet">
        <link href="/libs/codemirror-5.15.2/addon/dialog/dialog.css" rel="stylesheet">
        <script src="/libs/jquery-1.11.0-dist/jquery-1.11.0.js"></script>
        <script src="/libs/bootstrap-3.1.1-dist/js/bootstrap.js"></script>
        <script src="/libs/codemirror-5.15.2/codemirror.js"></script>
        <script src="/libs/codemirror-5.15.2/mode/markdown.js"></script>
        <script src="/libs/codemirror-5.15.2/keymap/vim.js"></script>
        <script src="/libs/codemirror-5.15.2/addon/dialog/dialog.js"></script>

        <link href="/css/markdown.css" rel="stylesheet">
        <link href="/css/pygments.css" rel="stylesheet">
        <link href="/css/markdown_edit.css" rel="stylesheet">
        <script src="/js/markdown_edit.js"></script>
    </head>

    <body style="background-color: rgb(204, 204, 204);">
        <form class="form-horizontal" method="post" action="/" name="markdown_input">
        <div style="position:fixed; top:0; bottom:0; left:0; right:0">
        
        <div style="margin-top:15px; margin-left:15px; margin-right:15px" id="head">{{!html_head}}</div>

        <div id="mdedit" style="position: absolute; height:40px; width:100%; top:0;" class="row">
            <div class="col-sm-6">
                <div style="margin:15px"  class="btn-toolbar"><div class="btn-group btn-group-sm">{{!in_actions}}</div>
                <div class="checkbox">
                    <label>
                      <input id="vim-mode-toggle" name="vim_mode" style="margin-left:0px;" type="checkbox" onchange="toggleVimMode(this)" {{!vim_mode}} />&nbsp;Vim mode
                    </label>
                </div></div>
            </div>
            <div style="padding-left:0px" class="col-sm-6">
                <div style="margin:15px" class="btn-toolbar"><div class="btn-group btn-group-sm">{{!out_actions}}</div></div>
            </div>
        </div>

        <div id="mdedit-body" style="padding:15px; position: absolute; top:0; bottom:0; left:0; right:0" class="row">
            <div style="height:100%" class="col-sm-6">
                <textarea style="font-family: monospace; font-size: small; color:#222; width:100%; height:100%" class="form-control" id="markdown_input" cols="80" rows="30" name="markdown_text">{{markdown_input}}</textarea>
            </div>
            <div style="height:100%; padding-left:0px" class="col-sm-6">
                <div class="html-output markdown-body" id="html_result" style="overflow: auto; height:100%"></div>
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
                        <div class="progress-bar" style="width: 100%;"></div>
                    </div>
                </div>
            </div>
          </div>
        </div>

    </body>
</html>
