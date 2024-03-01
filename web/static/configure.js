const pid_p_input = $("#pid_p")
const pid_i_input = $("#pid_i")
const pid_d_input = $("#pid_d")
const gyro_x_input = $("#gyro_x")
const gyro_y_input = $("#gyro_y")
const gyro_z_input = $("#gyro_z")
const accel_x_input = $("#accel_x")
const accel_y_input = $("#accel_y")
const accel_z_input = $("#accel_z")
const port_limit_input = $("#port_limit")
const stbd_limit_input = $("#stbd_limit")
const submit_pid_button = $("#submit_pid_button")
const reset_bias_button = $("#reset_bias_button")
const set_port_limit_button = $("#set_port_limit_button")
const set_stbd_limit_button = $("#set_stbd_limit_button")


fetch(
    $SCRIPT_ROOT + '/get_pid'
)
    .then(data => data.json())
    .then((json) => {
        pid_p_input.val(json.pid_p)
        pid_i_input.val(json.pid_i)
        pid_d_input.val(json.pid_d)
    });
submit_pid_button.on('click', function () {
    fetch(
        $SCRIPT_ROOT + '/set_pid',
        {
            headers: {"Content-Type": "application/json; charset=UTF-8"},
            method: "POST",
            body: JSON.stringify({pid_p: pid_p_input.val(), pid_i: pid_i_input.val(), pid_d: pid_d_input.val()})
        }
    ).then(
        fetch(
            $SCRIPT_ROOT + '/get_pid'
        )
            .then(data => data.json())
            .then((json) => {
                pid_p_input.val(json.pid_p)
                pid_i_input.val(json.pid_i)
                pid_d_input.val(json.pid_d)
            })
    );
});


fetch(
    $SCRIPT_ROOT + '/get_biases'
)
    .then(data => data.json())
    .then((json) => {
        gyro_x_input.val(json.gyro_x)
        gyro_y_input.val(json.gyro_y)
        gyro_z_input.val(json.gyro_z)
        accel_x_input.val(json.accel_x)
        accel_y_input.val(json.accel_y)
        accel_z_input.val(json.accel_z)
    });
reset_bias_button.on('click', function () {
    fetch(
        $SCRIPT_ROOT + '/reset_biases'
    ).then(
        fetch(
            $SCRIPT_ROOT + '/get_biases'
        )
            .then(data => data.json())
            .then((json) => {
                gyro_x_input.val(json.gyro_x)
                gyro_y_input.val(json.gyro_y)
                gyro_z_input.val(json.gyro_z)
                accel_x_input.val(json.accel_x)
                accel_y_input.val(json.accel_y)
                accel_z_input.val(json.accel_z)
            })
    );
});


fetch(
    $SCRIPT_ROOT + '/poll'
)
    .then(data => data.json())
    .then((json) => {
        port_limit_input.val(json.port_limit)
        stbd_limit_input.val(json.starboard_limit)
        if (json.port_limit > json.starboard_limit) alert("Port Limit should be less than Starboard Limit")
    });
set_port_limit_button.on('click', function () {
    fetch(
        $SCRIPT_ROOT + '/set_port_limit'
    ).then(
        fetch(
            $SCRIPT_ROOT + '/poll'
        )
            .then(data => data.json())
            .then((json) => {
                port_limit_input.val(json.port_limit)
                stbd_limit_input.val(json.starboard_limit)
                if (json.port_limit > json.starboard_limit) alert("Port Limit should be less than Starboard Limit")
            })
    );

});
set_stbd_limit_button.on('click', function () {
    fetch(
        $SCRIPT_ROOT + '/set_stbd_limit'
    ).then(
        fetch(
            $SCRIPT_ROOT + '/poll'
        )
            .then(data => data.json())
            .then((json) => {
                port_limit_input.val(json.port_limit)
                stbd_limit_input.val(json.starboard_limit)
                if (json.port_limit > json.starboard_limit) alert("Starboard Limit should be greater than Port Limit")
            })
    )
});