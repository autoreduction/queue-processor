steps = [
    {
        element: "#reduction_job_panel",
        title: "Run Summary",
        content: "Here you can see all the details for a given run including storage locations.",
        placement: "top"
    },
    {
        element: "#run_history",
        title: "Run History",
        content: "You can view the history of a run in more detail here.",
        placement: "bottom"
    },
    {
        element: "#show_reduction_logs",
        title: "Reduction logs",
        content: "If a problem occurred during the reduction process, it can be useful to view the " +
            "logs here to determine the cause.",
        placement: "bottom"
    },
    {
        element: "#re-run_and_graphs",
        title: "Re-run",
        content: "If available, you can select here to be begin manually submitting a re-run a job, entering a " +
            "description detailing the purpose of the re-run, changing any parameters if available.",
        placement: "top"
    },
];
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps = tourSteps.concat(steps)
}
