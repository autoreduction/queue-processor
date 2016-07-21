(function(){
    
    var runAction = function runAction()
    {
        var selectedRuns = $("[name='runCheckbox']").filter(':checked').map( function() {
            return [[$(this).attr('data-run_number'), $(this).attr('data-run_version'), $(this).attr('data-rb_number')]];
        }).get(); // a list of checked runs, each element of the form [run number, run version, RB number]
        
        // send POST to server to perform action
        var url = $(location).attr('href');
        var action = $('#runAction').val();
        var data = { "selectedRuns": JSON.stringify(selectedRuns), "action": action, csrfmiddlewaretoken: window.CSRF_TOKEN};
        $.post(url, data, postResponse);
    }

    var postResponse = function postResponse(data)
    {
        location.reload();
    }
    
    
    var toggleAllRuns = function toggleAllRuns()
    {
        $("[name='runCheckbox']").prop("checked", $('#selectAllRuns').is(":checked"));
    }
    
    var init = function init() 
    {
        $('#runActionButton').on('click', runAction);
        $('#selectAllRuns').on('click', toggleAllRuns);
    };

    init();
    
}())