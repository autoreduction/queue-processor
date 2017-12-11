(function(){
    var getIgnoredNotification = function getIgnoredNotification(){
        var ignoredNotifications = [];
        if(docCookies.getItem('ignoredNotifications')){
            ignoredNotifications = docCookies.getItem('ignoredNotifications').split(',');
        }
        return ignoredNotifications;
    };

    var notificationDismissed = function notificationDismissed(){
        var ignoredNotifications = getIgnoredNotification();
        ignoredNotifications.push($(this).data('notification-id'));
        docCookies.setItem('ignoredNotifications', ignoredNotifications.join(','), undefined, '/');
    };

    var showNotifications = function showNotifications(){
        var ignoredNotifications = getIgnoredNotification();
        $('.alert.hide').each(function(){
            var notificationId = $(this).data('notification-id').toString();
            if(ignoredNotifications.indexOf(notificationId) < 0){
                $(this).removeClass('hide');
            }
        });
    };

    var toggleIconOnCollapse = function toggleIconOnCollapse(){
        $('a[data-toggle="collapse"]').on('click.bs.collapse.data-api', function () {
            $(this).find('i').toggleClass('fa-chevron-down fa-chevron-right');
        });
    };

    var fixIeDataURILinks = function fixIeDataURILinks(){
        $("a[href]").each(function(){
            if($(this).attr('href').indexOf('data:image/jpeg;base64') === 0){
                var output = this.innerHTML;
                $(this).on('click', function openDataURIImage(event){
                    event.preventDefault();
                    var win = window.open("about:blank");
                    win.document.body.innerHTML = output;
                    win.document.title = document.title;
                });
            }
        });
    };

    var goBack = function goBack(event){
        event.preventDefault();
        history.back();
    };

    var init = function init(){
        $('.alert').on('closed.bs.alert', notificationDismissed);
        $('[data-toggle="popover"]').popover();
        $('body').on('click', '[data-toggle="popover"],[data-toggle="collapse"]', function(e){e.preventDefault(); return true;});
        $('a[href=#back]').on('click', goBack);
        showNotifications();
        toggleIconOnCollapse();
        if(isIE()){
            fixIeDataURILinks();
        }
    };

    init();
}());