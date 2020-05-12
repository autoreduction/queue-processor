steps = [
    {
        element: "#selectAllRuns",
        title: "selectAllRuns",
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