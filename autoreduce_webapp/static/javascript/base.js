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
        docCookies.setItem('ignoredNotifications', ignoredNotifications.join(','));
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

    var init = function init(){
        $('.alert').on('closed.bs.alert', notificationDismissed);

        showNotifications();
    };

    init();
}())