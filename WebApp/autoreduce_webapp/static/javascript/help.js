(function () {

    // Search all topics and filter them according to search terms and a category
    function filterHelpTopics(searchTerms, category) {
        $('section.help-topic, .no-results').hide();
        $('#topics-sidebar').removeClass('active');

        let i, searchTerm;
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
    }

    // Convert text in a topic heading to a dashed separated format
    function headingTextToDashed(headingText) {
        return headingText.replace(/[^a-z0-9\s]/gi, '').replace(/[_\s]/g, '-').toLowerCase();
    }

    // Generate a link for each topic heading and add the link also to the sidebar
    function generateSideNavLinks() {
        const sidenav = $('#sidenav-contents');
        $('.main-content section .panel-heading h3').each(function () {
            let id = headingTextToDashed($(this).text());
            let link = '<a href="#' + id + '">' + $(this).text() + '</a>';
            sidenav.append('<li>' + link + '</li>');
            $(this).html(link);
            $(this).attr("id", id);
        });
    }

    // Place search bar at the top when on mobile
    function mobileOnly() {
        $('#help-search').data('placement', 'top');
    }

    // Plain text input to array of terms
    function stringToSearchTerms(string) {
        return string.trim() && string.trim().split(' ');
    }

    // Converts text to string with escape special characters
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function init() {
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

            filterHelpTopics(stringToSearchTerms($(this).val()),
                $('#category-filter > .btn.active').data("category"));
        }).popover();

        // Filter by category on clicking toggle button
        $('#category-filter .btn').click(function () {
            filterHelpTopics(stringToSearchTerms($('#help-search').val()), $(this).data("category"));
        });

        // Show sidebar when hamburger menu clicked
        $('#hamburger-toggle').click(function () {
            $('#topics-sidebar').toggleClass('active');
        });

        // Reset search filters on clicking sidebar link
        $('#sidenav-contents').click(function () {
            $('[data-category="all"]').click();
            $('#help-search').val("");
            filterHelpTopics(stringToSearchTerms($(this).val()),
                $('#category-filter > .btn.active').data("category"));
        });

        generateSideNavLinks();

        // Scroll to anchor link after window loaded
        // 1 millisecond delay due to known chrome issue https://support.google.com/chrome/thread/11993079?hl=en
        $(window).load(function () {
            let hash = $(location).attr('hash');
            if (hash) {
                setTimeout(function () {
                    window.scroll(0, $(escapeRegExp(hash)).offset().top);
                }, 1);
            }
        });
    }

    init();
}());
