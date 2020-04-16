function setupTour(steps){
    tour = new Tour({
        steps: tourSteps,
        storage: false      // avoids storing process between visits
    })
    tour.init();
    tour.end();             // avoids bug where tour recognised as in progress on re-visit

    var tourButton = $("#tour-btn");
        if (tour.ended() == false){
            if (confirm("A tour is currently on going\nDo you wish to restart the tour?")){
                tour.restart();
                tour.end();
            }
        }
        tour.start(true);   // added 'true' arg forces start (alternative to localStorage.remove)
    });
};
