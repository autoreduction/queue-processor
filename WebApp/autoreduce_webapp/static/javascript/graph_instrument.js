var ctx = document.getElementById("chart").getContext('2d');

function getRunTitles() {
    return reductionRuns.map(x => (x.runNumber + '-' + x.runVersion));
}

function getData() {
    return reductionRuns.map(x => x.executionTime);

}

function getColours() {
    function getColour(status) {
        var red = 'rgba(255, 10, 50, 0.7)';
        var green = 'rgba(20, 255, 20, 0.7)';
        if (status === 'Completed') {
            return green;
        } else {
            return red;
        }
    }

    return reductionRuns.map(x => getColour(x.status));
}

function getStatus(runTitle) {
    var runNumber = runTitle.split('-')[0];
    var runVersion = runTitle.split('-')[1];
    return reductionRuns.filter(x => x.runNumber == runNumber && x.runVersion == runVersion).map(x => x.status);

}

function getCreated(runTitle) {
    var runNumber = runTitle.split('-')[0];
    var runVersion = runTitle.split('-')[1];
    return reductionRuns.filter(x => x.runNumber == runNumber && x.runVersion == runVersion).map(x => x.created);

}

var chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: getRunTitles(),
        datasets: [{
            label: 'Execution Time',
            data: getData(),
            backgroundColor: getColours(),
            borderWidth: 2
        }]

    },
    options: {
        onClick: graphClickEvent,
        scales: {
            yAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Execution time'
                },
                ticks: {
                    beginAtZero: true,
                    callback: function (value, index, values) {
                        return value + ' secs';
                    }
                }
            }],
            xAxes: [{
                stacked: false,
                beginAtZero: true,
                scaleLabel: {
                    display: true,
                    labelString: 'Run Number'
                },
                ticks: {
                    autoSkip: false
                }
            }],
        },
        tooltips: {
            mode: 'single',
            callbacks: {
                label: function (tooltipItem) {
                    return tooltipItem.yLabel + ' seconds';
                },

                afterBody: function (tooltipItem) {
                    var multistringText = ['Status: ' + getStatus(tooltipItem[0].xLabel)];
                    multistringText.push('Created: ' + getCreated(tooltipItem[0].xLabel));
                    return multistringText;
                }
            }
        },
        title: {
            display: true,
            text: instrument + ' Reduction Runs'
        },
        legend: {
            display: false
        }
    }
});

function graphClickEvent(evt) {
    var activeElement = chart.getElementAtEvent(evt);
    // Check we're clicking on a bar
    if (!activeElement.length) {
        return;
    }
    var label = activeElement[0]._model.label
    var win = window.open('/runs/' + instrument + '/' + label.replace('-', '/') + '/', '_blank');
}