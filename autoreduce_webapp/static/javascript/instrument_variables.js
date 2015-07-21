(function(){
    var deleteVariables = function deleteVariables(event){
        var url = $('#delete_url').val();
        var $form = $('#delete_variables');
        $.ajax({
            type: "POST",
            url: url,
            data: $form.serialize(),
            success: function(data) {
                window.location.reload()
            }
        });
    }
    var init = function init(){
        $('#delete_variables').on('click', '#deleteVariables', deleteVariables);
    };

    init();
}())