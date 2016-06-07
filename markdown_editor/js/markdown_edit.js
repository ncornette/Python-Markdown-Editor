var myCodeMirror;
var requestSend = false;
var isSending = false;

// Preventing Simultaneous ajax requests
// http://stackoverflow.com/a/8571903/3453164
function ajaxUpdatePreview() {
    requestSend = true;
    tryAjaxUpdatePreview();
}
function tryAjaxUpdatePreview() {
    if(!isSending && requestSend) {
        requestSend = false;
        isSending = true;
        $.ajax({
            type: "POST",
            url: "/ajax/preview",
            data: myCodeMirror.getValue(),
            contentType: "text/plain",
            success: function( data ) {
                isSending = false;
                setTimeout(tryAjaxUpdatePreview, 0);
                $("#html_result").html(data);
        }});
    }
}
function ajaxSaveFile() {
   $('#pleaseWaitDialog').modal('show')
   $.post( "/ajax/save", myCodeMirror.getValue())
        .done(function(data) {$('#pleaseWaitDialog').modal('hide')});
}
function ajaxVimMode(value) {
    $.ajax({
        type: "POST",
        url: "/ajax/vim_mode",
        data: JSON.stringify({vim_mode: value}),
        contentType: "application/json"});
}
function updateMarkdownInput(value) {
    myCodeMirror.setValue(value);
}

function toggleVimMode(e) {
    if (e.checked) {
        myCodeMirror.setOption('theme', '3024-night')
        myCodeMirror.setOption('vimMode', true)
        ajaxVimMode(true)
    } else {
        myCodeMirror.setOption('theme', 'neat')
        myCodeMirror.setOption('vimMode', false)
        ajaxVimMode(false)
    }
    myCodeMirror.focus()
}

$(document).ready(function() {

    // Setup custom header height
    head_height = $('#head').outerHeight(true);
    $('#mdedit').css('top', head_height+'px');
    $('#mdedit-body').css('top', (head_height+$('#mdedit').height())+'px');

    // Setup CodeMirror for markdown input
    CodeMirror.commands.save = function(instance) {ajaxSaveFile();}

    myCodeMirror = CodeMirror.fromTextArea(document.getElementById('markdown_input'), {
        value: "",
        mode: {name:"markdown",fencedCodeBlocks:true, underscoresBreakWords:false},
        indentUnit: "4",
        showCursorWhenSelecting: true,
        theme: "neat",
        vimMode: false
        });
    $(".CodeMirror").addClass("form-control");
    $(".CodeMirror").addClass("focusedInput");
    myCodeMirror.setSize("100%","100%");
    myCodeMirror.on("change", function(instance, changeObj) {ajaxUpdatePreview();});

    // Setup scrollbars sync
    var s1 = myCodeMirror.display.scrollbars.vert
    var s2 = $('#html_result')[0]

    function select_scroll(e) {
        viewHeight = s2.getBoundingClientRect().height
        ratio = (s2.scrollHeight-viewHeight)/(s1.scrollHeight-viewHeight)
        s2.scrollTop = s1.scrollTop*ratio;
    }

    s1.addEventListener('scroll', select_scroll, false);

    // Set Focus on markdown input
    $('#pleaseWaitDialog').on('hidden.bs.modal', function () {myCodeMirror.focus()})

    toggleVimMode(document.getElementById('vim-mode-toggle'));

    ajaxUpdatePreview();

});