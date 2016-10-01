var _replaceContext = false;        // replace the system context menu?
var _mouseOverContext = false;      // is the mouse over the context menu?
var _noContext = false;             // disable the context menu?
var _divContext;                    // makes my life easier

function InitContext()
{
    _divContext = document.getElementById('divContext');
    _divContext.onmouseover = function() { _mouseOverContext = true; };
    _divContext.onmouseout = function() { _mouseOverContext = false; };

    document.body.onmousedown = ContextMouseDown;
    document.body.oncontextmenu = ContextShow;
}
    
// call from the onMouseDown event, passing the event if standards compliant
function ContextMouseDown(event)
{
    if (_noContext || _mouseOverContext)
        return;

    // IE is evil and doesn't pass the event object
    if (event == null)
        event = window.event;

    // we assume we have a standards compliant browser, but check if we have IE
    var target = event.target != null ? event.target : event.srcElement;

    // only show the context menu if the right mouse button is pressed
    //   and a hyperlink has been clicked (the code can be made more selective)
    if (event.button == 2 && target.tagName.toLowerCase() == 'canvas' && activateMenu)
        _replaceContext = true;
    else if (!_mouseOverContext)
        _divContext.style.display = 'none';
}

function CloseContext()
{
    _mouseOverContext;
    _divContext.style.display = 'none';
}

// call from the onContextMenu event, passing the event
// if this function returns false, the browser's context menu will not show up
function ContextShow(event)
{
    if (_noContext || _mouseOverContext)
        return;

    // IE is evil and doesn't pass the event object
    if (event == null)
        event = window.event;

    // we assume we have a standards compliant browser, but check if we have IE
    var target = event.target != null ? event.target : event.srcElement;

    if (_replaceContext)
    {
        $('aContextNav').href = target.href;
        //   $('aAddWebmark').href = 'http://luke.breuer.com/webmark/?addurl=' +
        //       encodeURIComponent(target.href) + '&title=' +
        //       encodeURIComponent(target.innerHTML);

        // document.body.scrollTop does not work in IE
        var scrollTop = document.body.scrollTop ? document.body.scrollTop :
            document.documentElement.scrollTop;
        var scrollLeft = document.body.scrollLeft ? document.body.scrollLeft :
            document.documentElement.scrollLeft;

        // hide the menu first to avoid an "up-then-over" visual effect
        _divContext.style.display = 'none';
        _divContext.style.left = event.clientX + scrollLeft + 'px';
        _divContext.style.top = event.clientY + scrollTop + 'px';
        _divContext.style.display = 'block';

        _replaceContext = false;

        return false;
    }
}
