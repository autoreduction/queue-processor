(function(){

    var filterHelpTopics = function filterHelpTopics(event){
        if((event.keyCode || event.which || event.charCode) === 13){
            event.preventDefault();
            return;
        }
        var searchTerms = $(this).val().trim() && $(this).val().trim().split(' ');
        var i, searchTerm;
        if(searchTerms.length>0){
            for(i=0;i<searchTerms.length;i++){
                searchTerm = searchTerms[i].toLowerCase();
                $('section.help-topic,.no-results').hide();
                $('section.help-topic[data-topics*="'+searchTerm+'"').show();
                if($('section.help-topic:visible').length===0){
                    $('.no-results').show();
                }
            }
        }else{
            $('section.help-topic').show();
        }
    };

    var mobileOnly = function mobileOnly(){
        $('#help_search').data('placement', 'top');
    };

    var init = function init(){
        if(Math.max(document.documentElement.clientWidth, window.innerWidth || 0) < 767){
            mobileOnly();
        }
        $('#help_search').on('keyup', filterHelpTopics).popover();

    };

    init();
}());