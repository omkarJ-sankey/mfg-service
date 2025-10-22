const totalSalesConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: '£',
            data: data3,
            backgroundColor: [
                '#aFCA4F'
            ],
            borderColor: [
                '#9FCA4F'
            ],
            borderWidth: 1,
            barThickness: 14,
            borderRadius: 2,
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Sales(£)'
                }
            }
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#9FCA4F; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        }
    },
};

const chargingSessionsConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "Charging Sessions",
            data: data,
            fill: false,
            borderColor: "#3391C9",
            backgroundColor: "#3391C9",
            borderRadius: 2,
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#3391C9; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Number of sessions'
                }
            }
        }
    },
};
const newUsersConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "New Users",
            data: user_data,
            fill: false,
            borderColor: "#3391C9",
            backgroundColor: "#3391C9",
            borderRadius: 2,
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#3391C9; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Number of Users'
                }
            }
        }
    },
};

const activeUsersConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: 'Active Users',
            data: user_data,
            backgroundColor: [
                '#aFCA4F'
            ],
            borderColor: [
                '#9FCA4F'
            ],
            borderWidth: 1,
            barThickness: 14,
            borderRadius: 2,
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
                time: {
                    parser: 'MM/DD/YYYY',
                    tooltipFormat: 'MM/DD/YYYY'
                }
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Number of Users'
                }
            }
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#9FCA4F; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        }
    },
};


const powerConsumedConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "Power Consumed",
            data: data2,
            fill: false,
            borderColor: "#4C739E",
            backgroundColor: "#4C739E",
            borderRadius: 2,
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#4C739E; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';
                },

            }
        },
        scales: {

            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },

            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Power(kWh)'
                },
            }
        }
    },
};


const positiveRatingConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "5",
            data: ratings_five_data,
            fill: false,
            borderColor: "#3391C9",
            backgroundColor: "#3391C9",
            barThickness: 14
        },
        {
            label: "4",
            data: ratings_four_data,
            fill: false,
            borderColor: "#9FCA4F",
            backgroundColor: "#9FCA4F",
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'x',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[0].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + `<a style="color:${tooltipModel.labelColors[i].backgroundColor}; font-size:0.75rem; font-weight:bold">` + data[1] + '</a> ' + data[0] + ' Star Ratings' + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: 'Number of charging sessions'
                }
            }
        }
    },
};

const negativeRatingConfig = {
    type: 'line',
    data: {
        // labels: ["June", "July", "August", "September", "October"],
        datasets: [{
            label: "1",
            data: ratings_one_data,
            fill: false,
            borderColor: "#FF3B3B",
            backgroundColor: "#FF3B3B",
            barThickness: 14,
            borderRadius: 5,
        },
        {
            label: "2",
            data: ratings_two_data,
            fill: false,
            borderColor: "#FFB13B",
            backgroundColor: "#FFB13B",
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'x',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[0].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + `<a style="color:${tooltipModel.labelColors[i].backgroundColor}; font-size:0.75rem; font-weight:bold">` + data[1] + '</a> ' + data[0] + ' Star Ratings' + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: 'Number of charging sessions'
                }
            }
        }
    },
};

const NeutralRatingsConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: '3 star ratings',
            data: ratings_three_data,
            backgroundColor: [
                '#aFCA4F'
            ],
            borderColor: [
                '#9FCA4F'
            ],
            borderWidth: 1,
            barThickness: 14,
            borderRadius: 2,
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'index',
            intersect: false
        },
        hover: {
            onHover: function (e) {
                $("#canvas1").css("cursor", e[0] ? "pointer" : "default");
            }
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Number of charging sessions'
                }
            }
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[i].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + '<a style="color:#9FCA4F; font-size:0.75rem; font-weight:bold">' + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        }
    },
};

const loyaltyQRCodeConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "Purchased",
            data: purchased_loyalty_qr_data,
            fill: false,
            borderColor: "#3391C9",
            backgroundColor: "#3391C9",
            barThickness: 14
        },
        {
            label: "Redeemed",
            data: redeemed_loyalty_qr_data,
            fill: false,
            borderColor: "#9FCA4F",
            backgroundColor: "#9FCA4F",
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'x',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[0].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + `<a style="color:${tooltipModel.labelColors[i].backgroundColor}; font-size:0.75rem; font-weight:bold">` + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: 'Number of QR Codes'
                }
            }
        }
    },
};


const threeDSAnalyticConfig = {
    type: 'line',
    data: {
        datasets: [{
            label: "Success",
            data: successful_3ds_checks,
            fill: false,
            borderColor: "#9FCA4F",
            backgroundColor: "#9FCA4F",
            barThickness: 14
        },
        {
            label: "Failed",
            data: failed_3ds_checks,
            fill: false,
            borderColor: "#FF3B3B",
            backgroundColor: "#FF3B3B",
            barThickness: 14
        }]
    },
    options: {
        responsive: true,

        interaction: {
            mode: 'x',
            intersect: false
        },
        plugins: {
            legend: {
                align: 'start',
                display: false,
            },
            tooltip: {
                // Disable the on-canvas tooltip
                enabled: false,

                external: (context) => {
                    // Tooltip Element
                    var tooltipEl = document.getElementById('chartjs-tooltip');

                    // Create element on first render
                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div');
                        tooltipEl.id = 'chartjs-tooltip';
                        tooltipEl.innerHTML = '<table style="width: 100%; min-width:min-content;" ></table>';
                        document.body.appendChild(tooltipEl);
                    }

                    // Hide if no tooltip
                    var tooltipModel = context.tooltip;
                    if (tooltipModel.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return;
                    }

                    // Set caret Position
                    tooltipEl.classList.remove('above', 'below', 'no-transform');
                    if (tooltipModel.yAlign) {
                        tooltipEl.classList.add(tooltipModel.yAlign);
                    } else {
                        tooltipEl.classList.add('no-transform');
                    }

                    function getBody(bodyItem) {
                        return bodyItem.lines;
                    }

                    // Set Text
                    if (tooltipModel.body) {
                        var titleLines = tooltipModel.title || [];
                        var bodyLines = tooltipModel.body.map(getBody);
                        var innerHtml = '<thead>';

                        titleLines.forEach(function (title) {
                            innerHtml += '<tr style="border-bottom:solid 1px #EEEEEE;"><th style="font-weight:100;color:#666666;text-align: left;font-size:0.75rem;padding: 10px;">' + title + '</th></tr>';
                        });
                        innerHtml += '</thead><tbody>';

                        bodyLines.forEach((body, i) => {
                            var data = body[0].split(':');
                            var colors = tooltipModel.labelColors[i];
                            var style = 'background:' + colors.backgroundColor;
                            style += '; border-color:' + colors.borderColor;
                            style += '; border-width: 2px';
                            var span = '<span style="' + style + '"></span>';
                            innerHtml += '<tr><td style="padding: 10px;">' + span + `<a style="color:${tooltipModel.labelColors[i].backgroundColor}; font-size:0.75rem; font-weight:bold">` + data[1] + '</a> ' + data[0] + '</td></tr>';
                        });
                        innerHtml += '</tbody>';

                        var tableRoot = tooltipEl.querySelector('table');
                        tableRoot.innerHTML = innerHtml;
                    }

                    var position = context.chart.canvas.getBoundingClientRect();
                    var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                    // Display, position, and set styles for font
                    tooltipEl.style.opacity = 1;
                    tooltipEl.style.position = 'absolute';
                    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                    tooltipEl.style.font = bodyFont.string;
                    tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                    tooltipEl.style.pointerEvents = 'none';
                    tooltipEl.style.background = '#fff';
                    tooltipEl.style.borderRadius = '3px';
                    tooltipEl.style.boxShadow = '0px 0px 8px 0px rgba(0,0,0,0.1)';
                    tooltipEl.style.minHeight = '50px';
                    tooltipEl.style.minWidth = '150px';

                },

            }
        },
        scales: {

            x: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: xAxsLable
                },
            },
            y: {
                stacked: true,
                display: true,
                title: {
                    display: true,
                    text: 'Number of 3DS Transactions'
                }
            }
        }
    },
};

var TotalSalse;
var ChargingSessions;
var NewReg;
var PowerConsumed;
var ActiveUsers;
var PositiveRatings;
var NegativeRatings;
var NeutralRatings;
let LoyaltyQRCodes;
let threeDSAnalytics;

$("#line").click(function () {
    change('line', totalSalesConfig);
});

$("#bar").click(function () {
    change1('bar', totalSalesConfig);
});
//Charging Sessions
$("#show_trend_sessions").change(function () {
    if (this.checked) {
        changeChargingSessions('line', chargingSessionsConfig);
    } else {
        changeChargingSessions('bar', chargingSessionsConfig);
    }
});

//Salse
$("#show_trend_salse").change(function () {
    if (this.checked) {
        changeTotalSalse('line', totalSalesConfig);
    } else {
        changeTotalSalse('bar', totalSalesConfig);
    }
});

//Total Power Consumed
$("#show_trend_power").change(function () {
    if (this.checked) {
        changePowerConsumed('line', powerConsumedConfig);
    } else {
        changePowerConsumed('bar', powerConsumedConfig);
    }
});

$("#single_bar").change(function () {
    if (this.checked) {
        changeNewReg('line', newUsersConfig);
    } else {
        changeNewReg('bar', newUsersConfig);
    }
});

$("#single_bar_active").change(function () {
    if (this.checked) {
        changeActiveUser('line', activeUsersConfig);
    } else {
        changeActiveUser('bar', activeUsersConfig);
    }
});

$("#single_bar_neutral").change(function () {
    if (this.checked) {
        changeNuetralRatings('line', NeutralRatingsConfig);
    } else {
        changeNuetralRatings('bar', NeutralRatingsConfig);
    }
});
$("#single_bar_positive").change(function () {
    if (this.checked) {
        changePositiveRatings('line', positiveRatingConfig);
    } else {
        changePositiveRatings('bar', positiveRatingConfig);
    }
});
$("#single_bar_negative").change(function () {
    if (this.checked) {
        changeNegativeRatings('line', negativeRatingConfig);
    } else {
        changeNegativeRatings('bar', negativeRatingConfig);
    }
});
$("#single_bar_qr_codes").change(function () {
    if (this.checked) {
        changeLoyaltyQRCodeCount('line', loyaltyQRCodeConfig);
    } else {
        changeLoyaltyQRCodeCount('bar', loyaltyQRCodeConfig);
    }
});

$("#single_bar_3ds_analytics").change(function () {
    if (this.checked) {
        change3DSAnalyticsCount('line', threeDSAnalyticConfig);
    } else {
        change3DSAnalyticsCount('bar', threeDSAnalyticConfig);
    }
});
$("#curve_line").click(function () {
    change('line', config3);
});
$(document).ready(function () {
    changeChargingSessions('bar', chargingSessionsConfig);
    changeTotalSalse('bar', totalSalesConfig);
    changePowerConsumed('bar', powerConsumedConfig);

    changeNewReg('bar', newUsersConfig);
    changeActiveUser('bar', activeUsersConfig);

    changePositiveRatings('bar', positiveRatingConfig);
    changeNegativeRatings('bar', negativeRatingConfig);
    changeNuetralRatings('bar', NeutralRatingsConfig);
    changeLoyaltyQRCodeCount('bar', loyaltyQRCodeConfig);
    change3DSAnalyticsCount('bar', threeDSAnalyticConfig);
});

$("#multi_part_bar").click(function () {
    change1('bar', config4);
});

function changeTotalSalse(newType, config) {
    var ctx = document.getElementById(`canvas_total_salse`).getContext("2d");
    // Remove the old chart and all its event handles
    if (TotalSalse) {
        TotalSalse.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    TotalSalse = new Chart(ctx, temp);
}
function changePowerConsumed(newType, config) {
    var ctx = document.getElementById(`canvas_power_consumed`).getContext("2d");
    // Remove the old chart and all its event handles
    if (PowerConsumed) {
        PowerConsumed.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    PowerConsumed = new Chart(ctx, temp);

}
function changeChargingSessions(newType, config) {
    var ctx = document.getElementById(`canvas_sessions`).getContext("2d");
    // Remove the old chart and all its event handles
    if (ChargingSessions) {
        ChargingSessions.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    ChargingSessions = new Chart(ctx, temp);

}


function changeNewReg(newType, config) {
    var ctx = document.getElementById(`canvas_new_reg`).getContext("2d");
    // Remove the old chart and all its event handles
    if (NewReg) {
        NewReg.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    NewReg = new Chart(ctx, temp);
}
function changeActiveUser(newType, config) {
    var ctx = document.getElementById(`canvas_active_user`).getContext("2d");
    // Remove the old chart and all its event handles
    if (ActiveUsers) {
        ActiveUsers.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    ActiveUsers = new Chart(ctx, temp);

}

function changePositiveRatings(newType, config) {
    var ctx = document.getElementById(`canvas_positive_ratings`).getContext("2d");
    // Remove the old chart and all its event handles
    if (PositiveRatings) {
        PositiveRatings.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    PositiveRatings = new Chart(ctx, temp);

}

function changeNegativeRatings(newType, config) {
    var ctx = document.getElementById(`canvas_negative_ratings`).getContext("2d");
    // Remove the old chart and all its event handles
    if (NegativeRatings) {
        NegativeRatings.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    NegativeRatings = new Chart(ctx, temp);

}

function changeNuetralRatings(newType, config) {
    var ctx = document.getElementById(`canvas_neutral_ratings`).getContext("2d");
    // Remove the old chart and all its event handles
    if (NeutralRatings) {
        NeutralRatings.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    NeutralRatings = new Chart(ctx, temp);

}

function changeLoyaltyQRCodeCount(newType, config) {
    var ctx = document.getElementById(`canvas-qr-codes-loyalty`).getContext("2d");
    // Remove the old chart and all its event handles
    if (LoyaltyQRCodes) {
        LoyaltyQRCodes.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    LoyaltyQRCodes = new Chart(ctx, temp);

}


function change3DSAnalyticsCount(newType, config) {
    var ctx = document.getElementById(`canvas-three-ds-analytics`).getContext("2d");
    // Remove the old chart and all its event handles
    if (threeDSAnalytics) {
        threeDSAnalytics.destroy();
    }
    // Chart.js modifies the object you pass in. Pass a copy of the object so we can use the original object later
    var temp = jQuery.extend(true, {}, config);
    temp.type = newType;
    threeDSAnalytics = new Chart(ctx, temp);
}

