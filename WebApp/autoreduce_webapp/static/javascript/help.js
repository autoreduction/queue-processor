(function () {

    var searchFilter = function filterHelpTopics(searchTerms, category) {
        $('section.help-topic,.no-results').hide();

        var i, searchTerm;
        if (searchTerms.length > 0) {
            for (i = 0; i < searchTerms.length; i++) {
                searchTerm = searchTerms[i].toLowerCase();
                if (category === 'all') {
                    $('section.help-topic[data-topics*="' + searchTerm + '"]').show();
                } else {
                    $('section.help-topic[data-category*="' + category + '"]' +
                        '[data-topics*="' + searchTerm + '"]').show();
                }
            }

            if ($('section.help-topic:visible').length === 0) {
                $('.no-results').show();
            } else {
                $('.no-results').hide();
            }
        } else {
            if (category === "all") {
                $('section.help-topic').show();
            } else {
                $('section.help-topic[data-category*="' + category + '"').show();
            }

        }
    };

    var mobileOnly = function mobileOnly() {
        $('#help_search').data('placement', 'top');
    };

    var stringToSearchTerms = function stringToSearchTerms(string) {
        return string.trim() && string.trim().split(' ');
    };

    var init = function init() {
        if (Math.max(document.documentElement.clientWidth, window.innerWidth || 0) < 767) {
            mobileOnly();
        }

        $('#help_search').on('keyup', function (event) {
            if ((event.keyCode || event.which || event.charCode) === 13) {
                event.preventDefault();
                return;
            }

            searchFilter(stringToSearchTerms($(this).val()),
                $('#category-filter > .btn.active').data("category"));
        }).popover();

        $('#category-filter .btn').on('click', function () {
            var helpSearch = $('#help_search');
            searchFilter(stringToSearchTerms(helpSearch.val()), $(this).data("category"));
        });

    };

    init();
}());