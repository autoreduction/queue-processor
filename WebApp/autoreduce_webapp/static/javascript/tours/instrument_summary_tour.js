steps = [
    {
        element: "#not-active",
        title: "Instrument is not Active",
        content: "Here, we display whether or not the Instrument is active.",
        placement: "bottom"
    },
    {
        element: "#btn-instrument_active",
        title: "Instrument Active",
        content: "You can view details about the instrument when active here.",
        placement: "bottom"
    },
    {
        element: "#pause",
        title: "Pause Reduction",
        content: "Here, you are able to pause and unpause reduction for the instrument.",
        placement: "bottom"
    },
    {
        element: "#btn-re-run_past_job",
        title: "Re-running Past Jobs",
        content: "You can can re-run past jobs here.",
        placement: "bottom"
    },
    {
        element: "#btn-configure_new_runs",
        title: "Configuring New Runs",
        content: "To configure a new job, you can select this button.",
        placement: "bottom"
    },
    {
        element: "#btn-see_instrument_variables",
        title: "Instrument Variables",
        content: "You can view and configure instrument variables by selecting this button.",
        placement: "bottom"
    },
    {
        element: "#runs-table",
        title: "Runs Table",
        content: "This table displays all runs and their status in the reduction process.",
        placement: "bottom"
    },
    {
        element: "#run-row-top",
        title: "Runs Table",
        content: "Here you can view a runs status's and when the status was last updated.",
        placement: "bottom"
    },
    {
        element: "#top-run-number",
        title: "Runs Table",
        content: "To view an individual run in more detail, you can click on the run number to " +
            "be taken to a separate page.",
        placement: "right"
    },
    {
        element: "#filter-options",
        title: "Filters",
        content: "You can easily filter results returned using the options above.",
        placement: "bottom"
    },
    {
        element: "#filter_select",
        title: "Filters",
        content: "You can filter by run number or experiment here.",
        placement: "bottom"
    },
    {
        element: "#sort_select",
        title: "Filters",
        content: "You can filter by number of runs or date here.",
        placement: "bottom"
    },
    {
        element: "#pagination_select",
        title: "Filters",
        content: "If filtering by number, you can select the number of runs to display on each " +
            "page here.",
        placement: "bottom"
    },
    {
        element: "#apply_filters",
        title: "Filters",
        content: "Lastly, you can apply your filtered changes by selecting apply.",
        placement: "bottom"
    },
];
if (typeof tourSteps == 'undefined') {
    tourSteps = steps
}
else {
    tourSteps = tourSteps.concat(steps)
}