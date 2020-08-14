(function () {

    // Search all topics and filter them according to search terms and a category
    var searchFilter = function filterHelpTopics(searchTerms, category) {
        $('section.help-topic, .no-results').hide();

        var i, searchTerm;
        if (searchTerms.length > 0) {
            // Show all topics that match the category and the search term
            for (i = 0; i < searchTerms.length; i++) {
                searchTerm = searchTerms[i].toLowerCase();
                if (category === 'all') {
                    // Category is irrelevant here
                    $('section.help-topic[data-topics*="' + searchTerm + '"]').show();
                } else {
                    $('section.help-topic[data-category*="' + category + '"]' +
                        '[data-topics*="' + searchTerm + '"]').show();
                }
            }

            // If no help topics found show "no results" element
            if ($('section.help-topic:visible').length === 0) {
                $('.no-results').show();
            } else {
                $('.no-results').hide();
            }
        } else { // no search string entered
            if (category === "all") {
                $('section.help-topic').show();
            } else {
                $('section.help-topic[data-category*="' + category + '"').show();
            }

        }
    };

    // Convert text in a topic heading to a dashed separated format
    var headingTextToDashed = function headingTextToDashed(headingText) {
        return headingText.replace(/ +/g, '-').toLowerCase();
    };

    // Generate a link for each topic heading and add the link also to the sidebar
    var generateSideNavLinks = function generateSideNavLinks() {
        $('.main-content section .panel-heading h4').each(function () {
            var id = headingTextToDashed($(this).text());
            var link = '<a href="#' + id + '">' + $(this).text() + '</a>';
            $('#sidenav').append('<li>' + link + '</li>');
            $(this).html(link);
            $(this).attr("id", id);
        });
    };

    // Place search bar at the top when on mobile
    var mobileOnly = function mobileOnly() {
        $('#help-search').data('placement', 'top');
    };

    // Plain text input to array of terms
    var stringToSearchTerms = function stringToSearchTerms(string) {
        return string.trim() && string.trim().split(' ');
    };

    // Converts text to string with escape special characters
    var escapeRegExp = function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    };

    var init = function init() {
        if (Math.max(document.documentElement.clientWidth, window.innerWidth || 0) < 767) {
            mobileOnly();
        }

        // Trigger searching and remove popover on keyup event of search bar
        $('#help-search').on('keyup', function (event) {
            // Ignore pressing enter
            if ((event.keyCode || event.which || event.charCode) === 13) {
                event.preventDefault();
                return;
            }

            searchFilter(stringToSearchTerms($(this).val()),
                $('#category-filter > .btn.active').data("category"));
        }).popover();

        // Filter by category on clicking toggle button
        $('#category-filter .btn').click(function () {
            searchFilter(stringToSearchTerms($('#help-search').val()), $(this).data("category"));
        });

        // Show sidebar when hamburger menu clicked
        $('#hamburger-toggle').click(function () {
            $('#sidebar').toggleClass('active');
        });

        // Reset search filters on clicking sidebar link
        $('#sidenav').click(function () {
            $('[data-category="all"]').click();
            $('#help-search').val("");
            searchFilter(stringToSearchTerms($(this).val()),
                $('#category-filter > .btn.active').data("category"));
        });

        generateSideNavLinks();

        // Scroll to anchor link after window loaded
        // 1 millisecond delay due to known chrome issue https://support.google.com/chrome/thread/11993079?hl=en
        $(window).load(function () {
            var hash = $(location).attr('hash');
            if (hash) {
                setTimeout(function () {
                    window.scroll(0, $(escapeRegExp(hash)).offset().top);
                }, 1);
            }
        });
    };

    init();
}());