(function(){

    var showBy = function showBy(by){
        if(by !== 'by-experiment' && by !== 'by-run-number'){
            by = 'by-experiment';
        }
        if(by === 'by-experiment'){
            $('#by-experiment').removeClass('hide').addClass('active');
            $('#by-run-number').removeClass('active').addClass('hide');
            $('#by-experiment-tab').addClass('active');
            $('#by-run-number-tab').removeClass('active');
        }else if(by === 'by-run-number'){
            $('#by-run-number').removeClass('hide').addClass('active');
            $('#by-experiment').removeClass('active').addClass('hide');
            $('#by-run-number-tab').addClass('active');
            $('#by-experiment-tab').removeClass('active');
        }
        window.location.hash = '#' + by;
    };

    var tabClickAction = function tabClickAction(){
        var by = $(this).attr('href').replace('#','');
        showBy(by);
    };

    var toggleInstrumentsExperimentsClickAction = function toggleInstrumentsExperimentsClickAction(event){
        if($(this).is('a') && $(this).attr('href')==='#'){
            event.preventDefault();
        }
        $(this).find('i.fa').toggleClass('fa-chevron-right fa-chevron-down');
        $(this).parents('.instrument').find('.experiment,.run').toggleClass('hide');
    };
    var toggleExperimentRunsClickAction = function toggleExperimentRunsClickAction(event){
        if($(this).is('a') && $(this).attr('href')==='#'){
            event.preventDefault();
        }
        $(this).find('i.fa').toggleClass('fa-chevron-right fa-chevron-down');
        $(this).parents('.experiment').find('.experiment-runs').toggleClass('hide');
    };

    var init = function init(){
        var locationhash = window.location.hash.replace('#','');
        showBy(locationhash);

        $('#by-run-number-tab a,#by-experiment-tab a').on('click', tabClickAction);
        $('.instrument-heading').on('click', toggleInstrumentsExperimentsClickAction)
        $('.experiment-heading').on('click', toggleExperimentRunsClickAction)
    };

    init();
}());