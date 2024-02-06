
const courseIndicator = $("#course");
const headingIndicator = $("#heading");
const heelIndicator = $("#heel");
const bigDecButton = $("#bigDec");
const bigIncButton = $("#bigInc");
const smallDecButton = $("#smallDec");
const smallIncButton = $("#smallInc");
const tackDecButton = $("#tackDec");
const tackIncButton = $("#tackInc");
const messages = $("#messages");
// var onOffInput = $("#onOffInput");
const interfaceCheckbox = document.querySelector('#interfaceCheckbox');
const interfaceMessageArea = $("#interfaceMessageArea");
const rudderGaugeText = $("#rudder-gauge-text");
const rudderGaugeOpts = {
    angle: 0.15, // The span of the gauge arc
    lineWidth: 0.44, // The line thickness
    radiusScale: 1, // Relative radius
    pointer: {
        length: 0.65, // // Relative to gauge radius
        strokeWidth: 0.042, // The thickness
        color: '#000000' // Fill color
    },
    staticZones: [
        {strokeStyle: "#DB7B7B", min: -100, max: -1},
        {strokeStyle: "#75DB7B", min: 1, max: 100}
    ],
    divisions: 2,
    limitMax: false,     // If false, max value increases automatically if value > maxValue
    limitMin: false,     // If true, the min value of the gauge will be fixed
    colorStart: '#038024',   // Colors
    // colorStart: '#6FADCF',   // Colors
    colorStop: '#DA113A',    // just experiment with them
    // colorStop: '#8FC0DA',    // just experiment with them
    strokeColor: '#E0E0E0',  // to see which ones work best for you
    generateGradient: true,
    highDpiSupport: true,     // High resolution support
};
const rudderGaugeElement = document.getElementById('rudder-gauge');
const rudderGauge = new Gauge(rudderGaugeElement).setOptions(rudderGaugeOpts);
rudderGauge.maxValue = 100;
rudderGauge.setMinValue(-100);  // Prefer setter over gauge.minValue = 0
rudderGauge.animationSpeed = 10;
rudderGauge.set(0);

// Click handler definition
function onOffHandler() {
    console.log("Toggle Status")
    fetch($SCRIPT_ROOT + '/toggle_status');
}

function bigDecHandler() {
    console.log("Decrement " + bigDegrees)
    fetch($SCRIPT_ROOT + '/adjust_course/-'+bigDegrees);
}

function bigIncHandler() {
    console.log("Increment " + bigDegrees)
    fetch($SCRIPT_ROOT + '/adjust_course/+'+ bigDegrees);
}

function smallDecHandler() {
    console.log("Decrement " + smallDegrees)
    fetch($SCRIPT_ROOT + '/adjust_course/-' + smallDegrees);
}

function smallIncHandler() {
    console.log("Increment " + smallDegrees)
    fetch($SCRIPT_ROOT + '/adjust_course/+' + smallDegrees);
}

function tackDecHandler() {
    console.log("tack port")
    fetch($SCRIPT_ROOT + '/adjust_course/-' + tackDegrees);
}

function tackIncHandler() {
    console.log("tack starboard")
    fetch($SCRIPT_ROOT + '/adjust_course/+' + tackDegrees);
}


// Periodic status monitoring
(function () {
    $.getJSON(
        $SCRIPT_ROOT + "/poll",
        function (data) {
            if (interfaceCheckbox.checked) {
                interfaceMessageArea.text(
                    "plim=" + data.port_limit +
                    " slim=" + data.starboard_limit +
                    " motor=" + data.motor +
                    " rudder=" + data.rudder_position +
                    " raw-rudder=" + data.raw_rudder_position +
                    " control=" + data.control_output +
                    " turn_rate=" + data.turn_rate)
            } else {
                interfaceMessageArea.text("")
            }
            heelIndicator.text(data.heel);
            headingIndicator.text(data.heading);
            courseIndicator.text(data.course === "NAN" ? "---" : data.course);
            if (data.messages.startsWith("ERROR"))
                messages.prop('style', 'color:red');
            else
                messages.prop('style', 'color:blue');
            // messages.text(data.messages);  // TODO Add a monitor / debug page for this more raw output
            messages.text("Online")
            document.getElementById('onOffLed').style.backgroundColor = data.clutch_status ? "lightgreen" : "black";
            if (data.course !== "NAN") {
                bigDecButton.prop("value", "-" + bigDegrees);
                bigIncButton.prop("value", "+" + bigDegrees);
                smallDecButton.prop("value", "-" + smallDegrees);
                smallIncButton.prop("value", "+" + smallDegrees);
                tackDecButton.prop("value", "TACK PORT");
                tackIncButton.prop("value", "TACK STBD");
                bigDecButton.removeAttr("disabled");
                bigIncButton.removeAttr("disabled");
                smallDecButton.removeAttr("disabled");
                smallIncButton.removeAttr("disabled");
                tackDecButton.removeAttr("disabled");
                tackIncButton.removeAttr("disabled");
            } else {
                bigDecButton.prop("value", "---");
                bigIncButton.prop("value", "---");
                smallDecButton.prop("value", "---");
                smallIncButton.prop("value", "---");
                tackDecButton.prop("value", "---- ----");
                tackIncButton.prop("value", "---- ----");
                bigDecButton.prop("disabled", "true");
                bigIncButton.prop("disabled", "true");
                smallDecButton.prop("disabled", "true");
                smallIncButton.prop("disabled", "true");
                tackDecButton.prop("disabled", "true");
                tackIncButton.prop("disabled", "true");
            }
            rudderGaugeText.text(data.rudder_position)
            rudderGauge.set(data.rudder_position)
        }
    ).fail(function () {
        messages.prop('style', 'color:red');
        messages.text("Disconnected")
    });
    setTimeout(arguments.callee, timeout_ms); // Update every so often
})();