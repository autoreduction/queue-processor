(function () {
    if ($('#run_variables').length) {
        var originalFormUrl = $('#run_variables').attr('action');
    } else if ($('#instrument_variables').length) {
        var originalFormUrl = $('#instrument_variables').attr('action');
    } else if ($('#submit_jobs').length) {
        var originalFormUrl = $('#submit_jobs').attr('action');
    }

    var getForm = function getForm() {
        var $form = $('#run_variables');
        if ($form.length === 0) $form = $('#instrument_variables');
        if ($form.length === 0) $form = $('#submit_jobs');
        return $form;
    }

    var downloadScript = function downloadScript(event) {
        var submitAction = function submitAction() {
            var url = $('#preview_url').val();
            $form = getForm();
            $form.attr('action', url);
            window.onbeforeunload = undefined;
            $form.submit();
        };
        var cancelAction = function cancelAction() {
            return false;
        };
        event.preventDefault();
        if (validateForm()) {
            submitAction();
        } else {
            cancelAction();
        }
    };

    var validateForm = function validateForm() {
        var isValid = true;
        var errorMessages = [];
        var $errorList;
        $form = getForm();

        var resetValidationStates = function resetValidationStates() {
            $('.has-error').removeClass('has-error');
            $('.js-form-validation-message').hide();
        };

        var getVarName = function getVarName($input) {
            return '<strong>' + $input.attr('id').replace('var-standard-', '').replace('var-advanced-', '').replace('-', ' ') + '</strong>';
        };

        var addInvalid = function addInvalid($control, message) {
            $control.parent().addClass('has-error');
            isValid = false;
            errorMessages.push(message)
        };

        var validateRunRange = function validateRunRange() {
            var $start = $('#run_start');
            var $end = $('#run_end');
            var $experiment_reference = $('#experiment_reference_number');
            if ($start.length && $end.length && $experiment_reference.length) {
                if ($('#variable-range-toggle').length > 0 && !$('#variable-range-toggle').bootstrapSwitch('state')) {
                    validateNotEmpty.call($experiment_reference[0]);
                    if (!isNumber($experiment_reference.val())) {
                        addInvalid($experiment_reference, '<strong>Experiment Reference Number</strong> must be a number.')
                    }
                } else {
                    validateNotEmpty.call($start[0]);
                    var start_val = $start.val();
                    var end_val = $end.val();
                    if (!isNumber(start_val)) {
                        addInvalid($start, '<strong>Run start</strong> must be a number.')
                    }
                    if (end_val !== '' && !isNumber(end_val)) {
                        addInvalid($end, '<strong>Run finish</strong> can only be a number.')
                    }
                    if (parseInt(end_val) < parseInt(start_val) && parseInt(end_val) != 0) {
                        addInvalid($end, '<strong>Run finish</strong> must be greater than the run start.')
                    }
                }
            }
        };

        var validateNotEmpty = function validateNotEmpty() {

            if ($(this).val().trim() === '') {
                addInvalid($(this), getVarName($(this)) + ' is required.')
            }
        };
        var validateText = function validateText() {
        };
        var validateDescriptionText = function validateDescriptionText() {
            var max_length = 200;
            if ($(this).val().length >= max_length) {
                addInvalid($(this), 'Re-run description must be less than ' + max_length.toString() + ' characters.')
            }
        };
        var validateNumber = function validateNumber() {
            validateNotEmpty.call(this);
            if (!isNumber($(this).val())) {
                addInvalid($(this), getVarName($(this)) + ' must be a number.')
            }
        };
        var validateBoolean = function validateBoolean() {
            validateNotEmpty.call(this);
            if ($(this).val().toLowerCase() !== 'true' && $(this).val().toLowerCase() !== 'false') {
                addInvalid($(this), getVarName($(this)) + ' must be a boolean.')
            }
        };
        var validateListNumber = function validateListNumber() {
            var items, i;
            if ($(this).val().trim().endsWith(',')) {
                addInvalid($(this), getVarName($(this)) + ' must be a comma separated list.')
            } else if ($(this).val() !== '') {
                items = $(this).val().split(',');
                for (i = 0; i < items.length; i++) {
                    if (!isNumber(items[i])) {
                        addInvalid($(this), getVarName($(this)) + ' must be a comma separated list of numbers.')
                        break;
                    }
                }
            }
        };
        var validateListText = function validateListText() {
            var items, i;
            if ($(this).val().trim().endsWith(',')) {
                addInvalid($(this), getVarName($(this)) + ' must be a comma separated list.')
            } else if ($(this).val() !== '') {
                items = $(this).val().split(',');
                for (i = 0; i < items.length; i++) {
                    if (items[i].trim() === '') {
                        addInvalid($(this), getVarName($(this)) + ' must be a comma separated list.')
                        break;
                    }
                }
            }
        };
        var validateBatchRunRange = function validateBatchRunRange() {
            // Validates the batch re-run text
            validateNotEmpty.call(this);
            if ($(this).val().trim().endsWith(',')) {
                addInvalid($(this), '<strong>Run Numbers</strong> must be a comma separated list of either numbers or ranges.');
            }

            // Check all comma and '-' seperated elements
            comma_split_items = $(this).val().split(',');
            var still_valid = true
            for (i = 0; (i < comma_split_items.length) && still_valid; i++) {
                var all_split_items = comma_split_items[i].split('-');

                for (i = 0; i < all_split_items.length; i++) {
                    if (!isNumber(all_split_items[i])) {
                        addInvalid($(this), '<strong>Run Numbers</strong> must be a comma separated list of either numbers or ranges.');
                        still_valid = false
                        break;
                    }
                }
            }
        };

        // Finished validation at this point
        resetValidationStates();
        validateRunRange();
        $('#run_range').each(validateBatchRunRange);
        $form.find('[data-type="text"]').each(validateText);
        $form.find('[data-type="number"]').each(validateNumber);
        $form.find('[data-type="boolean"]').each(validateBoolean);
        $form.find('[data-type="list_number"]').each(validateListNumber);
        $form.find('[data-type="list_text"]').each(validateListText);
        $form.find('[name="run_description"]').each(validateDescriptionText);

        if (!isValid) {
            $('.js-form-validation-message').html('');
            $('.js-form-validation-message').append($('<p/>').text('Please fix the following error:'));
            $errorList = $('<ul/>');
            for (var i = 0; i < errorMessages.length; i++) {
                $errorList.append($('<li/>').html(errorMessages[i]));
            }
            $('.js-form-validation-message').append($errorList).show();
        }

        return isValid;
    };

    var triggerAfterRunOptions = function triggerAfterRunOptions() {
        if ($(this).val().trim() !== '') {
            $('#next_run').text(parseInt($(this).val()) + 1);
            $('#run_finish_warning').show();
        } else {
            $('#run_finish_warning').hide();
        }
    };

    var showDefaultSriptVariables = function showDefaultSriptVariables() {
        $('#default-variables-modal').modal();
    };

    var checkForConflicts = function checkForConflicts(successCallback) {
        var start = parseInt($('#run_start').val());
        var end = parseInt($('#run_end').val());
        var conflicts = [];
        if ($('#upcoming_runs').length > 0) {
            var upcoming = $('#upcoming_runs').val().split(',');
            for (var i = 0; i < upcoming.length; i++) {
                if (parseInt(upcoming[i]) >= start && (!end || upcoming[i] <= end)) {
                    conflicts.push(upcoming[i]);
                }
            }
        }
        if (conflicts.length === 0) {
            successCallback();
        } else {
            $('.js-conflicts-list').text(conflicts.join(','));
            $('#conflicts-modal .js-conflicts-confirm').unbind('click').on('click', successCallback);
            $('#conflicts-modal').modal();
        }
    };

    var submitForm = function submitForm(event) {
        var submitAction = function submitAction() {
            $form = getForm();
            $form.attr('action', originalFormUrl);
            window.onbeforeunload = undefined;

            //Set cursor to waiting
            $("body").css("cursor", "wait");
            $("#variableSubmit").css("cursor", "wait");
            $form.submit();
        };
        var cancelAction = function cancelAction() {
            return false;
        };

        event.preventDefault();
        if (validateForm()) {
            if ($('#variable-range-toggle').length > 0 && !$('#variable-range-toggle').bootstrapSwitch('state')) {
                $('#variable-range-toggle-value').val('False');
                $('#run_start').val('');
                $('#run_end').val('');
                submitAction();
            } else {
                $('#variable-range-toggle-value').val('True');
                $('#experiment_reference').val('');
                checkForConflicts(submitAction);
            }
        } else {
            cancelAction();
        }
    };

    var restrictFinished = function restrictFinished() {
        var $end = $('#run_end');
        var $start = $('#run_start');
        var setMin = function setMin() {
            $end.attr('min', $start.val());
        };
        $start.on('change', setMin);
        setMin();
    };

    var confirmUnsavedChanges = function confirmUnsavedChanges() {
        $form = getForm();
        $form.on('change', function () {
            $form.unbind('change');
            window.onbeforeunload = function confirmLeave(event) {
                if (!event) event = window.event;
                event.cancelBubble = true;
                event.returnValue = 'There are unsaved changes.';
                if (event.stopPropagation) {
                    event.stopPropagation();
                    event.preventDefault();
                }
            };

        });
    };

    var resetDefaultVariables = function resetDefaultVariables(event) {
        event.preventDefault();
        $form = getForm();
        $form.find('.js-variables-container').html($('.js-default-variables').html());
        $('#use_current_script').val("false");
        // We need to enable the popover again as the element is new
        $('[data-toggle="popover"]').popover();
    };

    var resetCurrentVariables = function resetCurrentVariables(event) {
        event.preventDefault();
        $form = getForm();
        //Set cursor to waiting
        $("body").css("cursor", "wait");
        $("#currentScript").css("cursor", "wait");

        if ($("#is_editing").length != 0) {
            $("#is_editing").val("false"); //Set this so new reduce_vars are picked up from script (bit of a hack)
        }

        //Update variables to those in reduce_vars
        $.get($('#updateURL').val(), function (data) {
            $form.find('.js-variables-container').html(data);
            $("body").css("cursor", "default");
            $("#currentScript").css("cursor", "pointer");

            // We need to enable the popover again as the element is new
            $('[data-toggle="popover"]').popover();
        });
        $('#use_current_script').val("true");
    };

    var toggleTrackScript = function toggleTrackScript(event) {
        var checkBox = $('#track_script_checkbox');
        checkBox.prop("checked", !checkBox.prop("checked"));
        updateTrackFields();
    };
    var updateTrackFields = function updateTrackFields() {
        // Lock the variable fields if they should track the script.
        var checkBox = $('#track_script_checkbox');
        $("[id^=var-]").attr("disabled", checkBox.prop("checked"));
    }

    var toggleActionExplainations = function toggleActionExplainations(event) {
        if (event.type === 'mouseover') {
            $('.js-action-explaination').text($(this).siblings('.js-explaination').text());
        } else if (event.type === 'mouseleave') {
            $('.js-action-explaination').text('');
        }
    };

    var updateBoolean = function updateBoolean(event) {
        var isChecked = $(this).prop('checked');
        if (isChecked) {
            isChecked = 'True';
        } else {
            isChecked = 'False';
        }
        $(this).val(isChecked).siblings('input[type=hidden]').val(isChecked);
    };

    var handleToggleSwitch = function handleToggleSwitch() {
        var toggleDisplay = function toggleDisplay(event, state) {
            if (state) {
                $('.js-variable-by-experiment').hide();
                $('.js-experiment-label').css('font-weight', 'normal').css('color', '#ccc');
                $('.js-variable-by-run').show();
                $('.js-run-label').css('font-weight', 'bold').css('color', '#000');
            } else {
                $('.js-variable-by-experiment').show();
                $('.js-experiment-label').css('font-weight', 'bold').css('color', '#000');
                $('.js-variable-by-run').hide();
                $('.js-run-label').css('font-weight', 'normal').css('color', '#ccc');
            }
        };

        $('.js-experiment-label,.js-run-label').css('cursor', 'default').css('font-weight', 'bold');
        toggleDisplay(undefined, $('#variable-range-toggle-value').val() === 'True');

        $('#variable-range-toggle').bootstrapSwitch();
        $('#variable-range-toggle').bootstrapSwitch('state', ($('#variable-range-toggle-value').val() === 'True'))
        $('#variable-range-toggle').on('switchChange.bootstrapSwitch', toggleDisplay);

        $('.js-experiment-label').on('click', function () {
            $('#variable-range-toggle').bootstrapSwitch('state', false);
        });

        $('.js-run-label').on('click', function () {
            $('#variable-range-toggle').bootstrapSwitch('state', true);
        });

    };

    var init = function init() {
        $('#script-preview-modal').on('click', '#downloadScript', downloadScript);

        $('#run_variables,#instrument_variables').on('click', '#resetValues', resetDefaultVariables);
        $('#run_variables,#instrument_variables,#submit_jobs').on('click', '#currentScript', resetCurrentVariables);
        $('#run_variables,#instrument_variables,#submit_jobs').on('click', '#variableSubmit', submitForm);
        $('#run_variables,#instrument_variables').on('click', 'input[type=checkbox][data-type=boolean]', updateBoolean);

        $('#instrument_variables').on('click', '#track_script', toggleTrackScript);
        $('#instrument_variables').on('click', '#track_script_checkbox', updateTrackFields);
        updateTrackFields();

        $('#instrument_variables').on('mouseover mouseleave', '#track_script', toggleActionExplainations);
        $('.js-form-actions li>a').on('mouseover mouseleave', toggleActionExplainations);

        $('#run_end').on('change', triggerAfterRunOptions);
        $('.js-show-default-variables').on('click', showDefaultSriptVariables);
        if ($('#variable-range-toggle').length > 0) {
            handleToggleSwitch();
        }
        restrictFinished();
        confirmUnsavedChanges();
    };

    init();
}())