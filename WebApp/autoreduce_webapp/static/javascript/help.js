(function () {
    const topicsJson = getTopicJsons();

    // Fuzzy search topics (header and body text) with searchText and a category
    // making the matching topics visible on the page.
    function filterHelpTopics(searchText, category) {
        $('section.help-topic, .no-results').hide();
        $('#topics-sidebar').removeClass('active');

        // Show all topics in category by default without searchText
        if (searchText === "") {
            if (category === "all") {
                $('section.help-topic').show();
            } else {
                $(`section.help-topic[data-category*="${category}"`).show();
            }
            return;
        }

        const fuse = new Fuse(topicsJson, {
            keys: ['title', 'body'],
            threshold: 0.2,
            ignoreLocation: true
        });

        const result = fuse.search(searchText);
        for (const topic of result) {
            if (category === "all" || topic.item.category === category) {
                $(topic.item.selector).show();
            }
        }

        // If no help topics found show "no results" element
        if ($('section.help-topic:visible').length === 0) {
            $('.no-results').show();
        } else {
            $('.no-results').hide();
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
            let link = `<a href="#${id}">${$(this).text()}</a>`;
            sidenav.append('<li>' + link + '</li>');
            $(this).html(link);
            $(this).attr("id", id);
        });
    }

    // Converts text to string with escape special characters
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    // Return a json of the topics on the page.
    // Formatted: [{selector, title, body, category}, ...]
    function getTopicJsons() {
        let topics = [];
        $('section.help-topic').each(function (i, topicElementSelector) {
            const topicElement = $(topicElementSelector);
            topics.push({
                "selector": topicElementSelector,
                "title": topicElement.find('.panel-heading').text(),
                "body": topicElement.find('.panel-body').text(),
                "category": topicElement.data("category")
            });
        });

        return topics;
    }

    function init() {
        hljs.highlightAll();

        // Trigger searching and remove popover on keyup event of search bar
        $('#help-search').on('keyup', function (event) {
            // Ignore pressing enter
            if ((event.keyCode || event.which || event.charCode) === 13) {
                event.preventDefault();
                return;
            }

            filterHelpTopics($(this).val(),
                $('#category-filter > .btn.active').data("category"));
        }).popover();

        // Filter by category on clicking toggle button
        $('#category-filter .btn').click(function () {
            filterHelpTopics($('#help-search').val(), $(this).data("category"));
        });

        // Show sidebar when hamburger menu clicked
        $('#hamburger-toggle').click(function () {
            $('#topics-sidebar').toggleClass('active');
        });

        // Reset search filters on clicking sidebar link
        $('#sidenav-contents').click(function () {
            $('[data-category="all"]').click();
            $('#help-search').val("");
            filterHelpTopics($(this).val(),
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
