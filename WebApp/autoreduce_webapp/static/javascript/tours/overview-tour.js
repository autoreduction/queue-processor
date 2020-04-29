var firstInstrumentBtn = $("[id*='-instrument-btn']")[0];
steps = [
    {
        element: "#instrument-btns-container",
        title: "Instruments",
        content: "Here are ISIS instruments connected to autoreduction.",
        placement: "bottom"
    },
    {
        element: "#"+firstInstrumentBtn.id,
        title: "Instruments",
        content: "You can click on an instrument to view its reduction jobs.",
        placement: "right"
    },
]
if (typeof tourSteps == 'undefined'){
    tourSteps = steps
}
else{
    tourSteps.concat(steps)
}