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
            if(ignoredNotifications.indexOf($(this).data('notification-id')) < 0){
                $(this).show();
            }
        });
    };

    var init = function init(){
        $('.alert-dismissible').on('closed.bs.alert', notificationDismissed);

        showNotifications();
    };

    init();
}())