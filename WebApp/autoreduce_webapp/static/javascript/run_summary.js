(function(){
    var showHistory = function showHistory(event){
        $('.run-history').modal();
    };
    
    var showLogs = function showHistory(event){
        $('.log-display').modal();
    };

    var init = function init(){
        $('.js-reduction-run-history').on('click', showHistory);
        $('.js-log-display').on('click', showLogs);
    };

    init();
}())