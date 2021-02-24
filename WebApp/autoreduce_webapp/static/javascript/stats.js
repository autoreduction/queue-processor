var ctx = document.getElementById("chart").getContext('2d');

function getStatusNames() {
    return statuses.map(x => x.name);
}

function getStatusCounts() {
    return statuses.map(x => x.count);
}

function getColours() {
    return [
        '#ff1500',
        '#00aeff',
        '#31708f',
        '#00c93c'
    ];
}

var chart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: getStatusNames(),
        datasets: [{
            label: 'Execution Time',
            data: getStatusCounts(),
            backgroundColor: getColours(),
            borderWidth: 2
        }]

    },
    options: {
        title: {
            display: true,
            text: 'Reduction Runs'
        },
        legend: {
            display: true
        },
        responsive: true

    }
});

function graphClickEvent(evt) {
    var activeElement = chart.getElementAtEvent(evt);
    // Check we're clicking on a bar
    if (!activeElement.length) {
        return;
    }
    label = activeElement[0]._model.label
    var win = window.open('/runs/' + instrument + '/' + label.replace('-', '/') + '/', '_blank');
}
