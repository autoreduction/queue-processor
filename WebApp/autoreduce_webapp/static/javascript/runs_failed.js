(function(){
    
    var runAction = function runAction()
    {
        
        // set form values
        var action = $('#runAction').val();
        $("[name='action']").attr('value', action);
        
        var selectedRuns = $(".runCheckbox").filter(':checked').map( function() {
            return [[$(this).attr('data-run_number'), $(this).attr('data-run_version'), $(this).attr('data-rb_number')]];
        }).get(); // a list of checked runs, each element of the form [run number, run version, RB number]
        $("[name='selectedRuns']").attr('value', JSON.stringify(selectedRuns));
        
        
        //Set cursor to waiting
        $("body").css("cursor", "wait");
        $("#variableSubmit").css("cursor", "wait");
        
        
        // send POST to server to perform action
        window.onbeforeunload = undefined;
        var url = $(location).attr('href');
        var aForm = $("#actionForm")
        aForm.attr("action", url);
        aForm.submit();
    };
    
    
    
    var toggleAllRuns = function toggleAllRuns()
    {
        $(".runCheckbox").prop("checked", $('#selectAllRuns').is(":checked"));
    }
    
    var init = function init() 
    {
        $('#runActionButton').on('click', runAction);
        $('#selectAllRuns').on('click', toggleAllRuns);
    };

    init();
    
}())