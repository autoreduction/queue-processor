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
            $('#by-tabs-mobile').val(by);
        }else if(by === 'by-run-number'){
            $('#by-run-number').removeClass('hide').addClass('active');
            $('#by-experiment').removeClass('active').addClass('hide');
            $('#by-run-number-tab').addClass('active');
            $('#by-experiment-tab').removeClass('active');
            $('#by-tabs-mobile').val(by);
        }
        window.location.hash = '#' + by;
    };

    var tabClickAction = function tabClickAction(){
        var by = $(this).attr('href').replace('#','');
        showBy(by);
    };
    var mobileTabChangeAction = function mobileTabChangeAction(){
        var by = $(this).val();
        showBy(by);
    };

    var toggleInstrumentsExperimentsClickAction = function toggleInstrumentsExperimentsClickAction(event){
        if(($(event.target).is('a') && $(event.target).attr('href')==='#') || $(event.target).is(':not(a)')){
            event.preventDefault();
            $(this).find('i.fa').toggleClass('fa-chevron-right fa-chevron-down');
            $(this).parents('.instrument').find('.experiment,.run').toggleClass('hide');
        }
    };
    var toggleExperimentRunsClickAction = function toggleExperimentRunsClickAction(event){
        if(($(event.target).is('a') && $(event.target).attr('href')==='#') || $(event.target).is(':not(a)')){
            event.preventDefault();
            $(this).find('i.fa').toggleClass('fa-chevron-right fa-chevron-down');
            $(this).parents('.experiment').find('.experiment-runs').toggleClass('hide');
        }
    };

    var run_search = function run_search(event){
        if((event.keyCode || event.which || event.charCode) === 13){
            event.preventDefault();
            return;
        }
        $('#no-search-results, .instrument, .instrument .instrument-heading, .instrument .experiment-heading, .instrument .run-row, .no-results').hide();
        var $matches = $('div>a:contains('+$(this).val()+')');
        $matches.each(function(){
            var updateHidden = function($this){
                return function(){
                    $this.parents('.instrument').removeClass('hide').show().find('.instrument-heading').removeClass('hide').show();
                    $this.parents('.experiment,.run').removeClass('hide').show();
                    $this.parents('.experiment').find('.experiment-heading,.experiment-runs').removeClass('hide').show();
                    $this.parents('.run-row').removeClass('hide').removeClass('hide').show();
                };
            }($(this));
            // We're using fastdom to avoid any possible DOM thrashing.
            fastdom.write(updateHidden);
        });
        if($matches.length === 0){
            $('#no-search-results').removeClass('hide').show();
        }
    };

    var mobileOnly = function mobileOnly(){
        $('#run_search').data('position', 'top');
    };

    var init = function init(){
        var locationhash = window.location.hash.replace('#','');
        showBy(locationhash);
        if(Math.max(document.documentElement.clientWidth, window.innerWidth || 0) < 767){
            mobileOnly();
        }

        $('#run_search').on('keyup', run_search);
        $('#by-run-number-tab a,#by-experiment-tab a').on('click', tabClickAction);
        $('#by-tabs-mobile').on('change', mobileTabChangeAction);
        $('.instrument-heading').on('click', toggleInstrumentsExperimentsClickAction)
        $('.experiment-heading').on('click', toggleExperimentRunsClickAction)
    };

    init();
}());