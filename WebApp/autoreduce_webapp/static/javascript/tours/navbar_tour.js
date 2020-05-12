steps = [
    {
        element: "#navbar_links",
        title: "Navigation Bar",
        content: "Lastly, you can also use the navigation bar to go to different pages.",
        placement: "left"
    }
]
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps = tourSteps.concat(steps)
}
