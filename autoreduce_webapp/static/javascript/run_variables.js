(function(){
    var formUrl = $('#run_variables').attr('action');

    var isNumber = function isNumber(n){
        return !isNaN(parseFloat(n)) && isFinite(n);
    };

    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };

    var previewScript  = function previewScript(){
        var url = $('#preview_url').val();
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');
        $form.attr('action', url);
        $form.submit();
    };

    var validateForm = function validateForm(event){
        var isValid = true;
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');

        var resetValidationStates = function resetValidationStates(){
            $('.has-error').removeClass('has-error');
        };

        var validateNotEmpty = function validateNotEmpty(){
            if($(this).val().trim() === ''){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateText = function validateText(){
            validateNotEmpty.call(this);
        };
        var validateNumber = function validateNumber(){
            validateNotEmpty.call(this);
            if(!isNumber($(this).val())){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateBoolean = function validateBoolean(){
            validateNotEmpty.call(this);
            if($(this).val().toLowerCase() !== 'true' && $(this).val().toLowerCase() !== 'false'){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateListNumber = function validateListNumber(){
            var items, i;
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(i=0;i<items.length;i++){
                    if(!isNumber(items[i])){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };
        var validateListText = function validateListText(){
            var items, i;
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(i=0;i<items.length;i++){
                    if(items[i].trim() === ''){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };

        // Populate all boolean values with their checked state
        $('[data-type="boolean"]').each(function(){
            if($(this).attr('checked')){
                $(this).val('True');
            }else{
                $(this).val('False');
            }
        });

        resetValidationStates();
        $('[data-type="text"]').each(validateText);
        $('[data-type="number"]').each(validateNumber);
        $('[data-type="boolean"]').each(validateBoolean);
        $('[data-type="list_number"]').each(validateListNumber);
        $('[data-type="list_text"]').each(validateListText);

        event.preventDefault();
        if(isValid){
            $form.attr('action', formUrl);
            $form.submit();
        }else{
            return false;
        }
    };

    var triggerAfterRunOptions = function triggerAfterRunOptions(){
        if($(this).val().trim() !== ''){
            $('#next_run').text(parseInt($(this).val())+1);
            $('#run_finish_warning').show();
        }
    };

    var showDefaultSriptVariables = function showDefaultSriptVariables(){
        $('#default-variables-modal').modal();
    };
    
    var init = function init(){
        $('#previewScript').on('click', previewScript);
        $('#variableSubmit').on('click', validateForm);
        $('#run_end').on('change', triggerAfterRunOptions);
        $('.js-show-default-variables').on('click', showDefaultSriptVariables);
    };

    init();
}())