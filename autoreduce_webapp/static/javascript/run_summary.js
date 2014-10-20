(function(){
    var showHistory = function showHistory(event){
        $('.run-history').modal();
    };

    var init = function init(){
        $('.js-reduction-run-history').on('click', showHistory);
    };

    init();
}())