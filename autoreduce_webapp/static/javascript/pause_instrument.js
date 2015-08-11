(function(){

    var resume_html = 'Resume<span class="hidden-sm hidden-md"> Instrument</span>';
    var pause_html = 'Pause<span class="hidden-sm hidden-md"> Instrument</span>';

    var toggleInstrument = function toggleInstrument(event){
        var $form = $(event.currentTarget.nextElementSibling);
        $("body").css("cursor", "wait");
        event.stopImmediatePropagation();
        $(event.currentTarget).css("cursor", "wait");
        $.ajax({
            url : $form.attr('action'),
            type: "POST",
            data: $form.serialize(),
            success: function (data) {
                $form.find("#currently_paused").val(data["currently_paused"]);
                $(event.currentTarget).find("i.fa").toggleClass("fa-pause fa-play");

                var current_text_obj = $(event.currentTarget).find("span.hidden-xs");
                if (current_text_obj.html() == resume_html) {
                    current_text_obj.html(pause_html);
                } else {
                    current_text_obj.html(resume_html);
                };

                $("body").css("cursor", "default");
                $(event.currentTarget).css("cursor", "pointer");
            }
        })
    };

    var init = function init(){
        $("[id^='pause']").on('click', toggleInstrument);
    };

    init();
}());