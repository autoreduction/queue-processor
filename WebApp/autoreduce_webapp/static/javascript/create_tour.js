(function(){
    function setupTour(steps){
        const tour = new Tour({
            steps: steps,
            storage: false,      // avoids storing process between visits
            backdrop: true,
            backdropPadding: 2
        });
        tour.init();
        tour.end();             // avoids bug where tour recognised as in progress on re-visit

        const tourButton = $("#tour-btn");
        tourButton.click(function(){
            if (tour.ended()){
                tour.restart();
            }
            else {
                if (confirm("A tour is currently on going\nDo you wish to restart the tour?")){
                    tour.restart();
                    tour.end();
                }
            }
            tour.start(true);   // added 'true' arg forces start (alternative to localStorage.remove)
        });
    }

    const init = function init() {
        document.getElementById('right_of_title').innerHTML = '<button class="btn btn-info btn-block" id="tour-btn">Take a tour</button>';
        setupTour(tourSteps);
    };

    init();
}());



