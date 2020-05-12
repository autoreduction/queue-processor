steps = [
    {
        element: "#run-number-title",
        title: "Run Number",
        content: "Each reduction job is given a unique 'run number', shown in this column.\n \
                  When the same data is reduced again (a re-run) an additional number is appended \
                  denoting each different version.",
        placement: "top"
    },
    {
        element: "#instrument-title",
        title: "Instrument",
        content: "...",
        placement: "top"
    },
    {
        element: "#status-title",
        title: "Status",
        content: "...",
        placement: "top"
    },
    {
        element: "#submitted-title",
        title: "Submitted",
        content: "...",
        placement: "top"
    },
    {
        element: "#submitted-by-title",
        title: "Submitted By",
        content: "...",
        placement: "top"
    },
]
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps = tourSteps.concat(steps)
}