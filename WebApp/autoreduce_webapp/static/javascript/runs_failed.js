(function(){

    const runAction = function runAction() {

        // set form values
        let action = $('#runAction').val();
        $("[name='action']").attr('value', action);

        let selectedRuns = $(".runCheckbox").filter(':checked').map(function () {
            return [[$(this).attr('data-run_number'), $(this).attr('data-run_version'), $(this).attr('data-rb_number')]];
        }).get(); // a list of checked runs, each element of the form [run number, run version, RB number]
        $("[name='selectedRuns']").attr('value', JSON.stringify(selectedRuns));


        //Set cursor to waiting
        $("body").css("cursor", "wait");
        $("#variableSubmit").css("cursor", "wait");


        // send POST to server to perform action
        window.onbeforeunload = undefined;
        let url = $(location).attr('href');
        let aForm = $("#actionForm")
        aForm.attr("action", url);
        aForm.submit();
    };


    const toggleAllRuns = function toggleAllRuns()
    {
        $(".runCheckbox").prop("checked", $('#selectAllRuns').is(":checked"));
    }
    
    const init = function init()
    {
        $('#runActionButton').on('click', runAction);
        $('#selectAllRuns').on('click', toggleAllRuns);
    };

    init();
    
}())