steps = [
    {
        element: "#navbar_container",
        title: "Navigation Bar",
        content: "Lastly, you can also use the navigation bar to go to different pages."
    }
]
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps = tourSteps.concat(steps)
}
