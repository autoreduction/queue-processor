if ($("#navbar-username").length == 0){     // if there is no element with id="navbar-username"
    var content = "Lastly, you can sign in to access additional pages."
}
else{
    var content = "Lastly, you can also use the navigation bar to go to different pages."
}

steps = [
    {
        element: "#navbar_links",
        title: "Navigation Bar",
        content: content,
        placement: "left"
    }
]
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps = tourSteps.concat(steps)
}
