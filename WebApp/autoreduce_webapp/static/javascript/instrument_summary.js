(function(){
    var init = function init(){
        var select = document.getElementById('filter_select');
        select.onchange = function(){
            document.getElementById('filter_options').submit();
        };

    };

    init();
}())