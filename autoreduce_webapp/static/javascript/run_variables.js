(function(){
    var formUrl = $('#run_variables').attr('action');

    var previewScript  = function previewScript(){
        var url = $('#preview_url').val();
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');
        $form.attr('action', url);
        $form.submit();
    };

    var validateForm = function validateForm(){
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');
        // TODO: Check all form input for valid types
        $form.attr('action', formUrl);
        $form.submit();
    };

    var init = function init(){
        $('#previewScript').on('click', previewScript);
        $('#variableSubmit').on('click', validateForm);
    };

    init();
}())