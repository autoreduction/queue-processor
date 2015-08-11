(function(){

    var toggleInstrument = function toggleInstrument(event){
        var form = event.currentTarget.nextElementSibling;
        form.submit();
    };

    var init = function init(){
        $("[id^='pause']").on('click', toggleInstrument);
    };

    init();
}());