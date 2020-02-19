(function(){
    function setProgressCursor(elem) {
        elem.css('cursor', 'progress');
        $('body').css('cursor', 'progress');
    }
    function setDefaultCursor(elem) {
        elem.css('cursor', '');
        $('body').css('cursor', '');
    }

    var init = function init(){
        document.addEventListener("DOMContentLoaded", function(){
            setDefaultCursor($(this));
        });

        var select = document.getElementById('filter_select');
        select.onchange = function(){
            setProgressCursor($(this));
            document.getElementById('filter_options').submit();
        };

        var apply = document.getElementById('apply_filters');
        apply.onclick = function(){
            setProgressCursor($(this));
        }
    };

    init();
}())