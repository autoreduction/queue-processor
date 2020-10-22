if ($("#navbar-username").length == 0){     // if there is no element with id="navbar-username"
    var content = "You can sign in to access additional pages."
}
else{
    var content = "You can use the navigation bar to go to different pages."
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
