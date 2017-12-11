(function(){
    var deleteVariables = function deleteVariables(event){
        var $form = $('#delete_variables');
        $form.submit();
    }
    var init = function init(){
        $('#delete_variables').on('click', '#deleteVariables', deleteVariables);
    };

    init();
}())