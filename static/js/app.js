const queueList = document.getElementById('queue-list');
const queueForm = document.getElementById('queue-form');
const itemNameInput = document.getElementById('item-name');
const sampleNumberInput = document.getElementById('sample-number');
const startButton = document.getElementById('queue-start-button');

// Queue variables
let queueItems_array = [];      // Array to store the queue items
let queueRunningItem = null;    // Variable to store the currently running item
let queue_paused = true;       // Flag to indicate if the queue is paused


const MAX_TEMP = 1100; // Maximum temperature for the furnace

// Initialize SortableJS on the queue list
const sortable = new Sortable(queueList, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: function (evt) {
        const movedItem = queueItems_array.splice(evt.oldIndex, 1)[0]; // Remove the item from the old index
        queueItems_array.splice(evt.newIndex, 0, movedItem);          // Insert it at the new index
        renderQueue(); // Re-render the queue to reflect changes
    }
});

setInterval(() => {
    

    // Get the system state from the Flask endpoint
    let systemState = [];
    $.ajax({
        url: '/api/get_state',
        method: 'GET',
        async: false,
        success: function (data) {
            systemState = data;
        }
    });
    console.log(systemState);
    console.log(systemState.aish_experiment == null);
    console.log(queue_paused);


    // Update the system state on the page
    renderQueue();
    renderCurrentlyRunning(systemState);

    // Check if the queue is paused, and if the system is ready to run the next item
    // If the queue is not paused and the system is ready, send the next item in the queue
    if (!queue_paused && systemState.aish_experiment == null) {
        console.log('Sending next item in queue.');
        sendNextQueueItem();
    }

  }, 2000);
  

$(document).ready(function () {
    // Initialize Bootstrap tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Bind Button callbacks
    // Queue
    $('#queue-form').on('submit', handle_button_queueAdd);
    $('#queue-start-button').on('click', handle_button_queueStart);

    // Manual Control (AISH Sample Loader)
    $('#manualControl-loadButton').on('click', handle_button_manualLoading);
    $('#manualControl-unloadButton').on('click', handle_button_manualUnloading);
    $('#manualControl-loadBufferButton').on('click', handle_button_sampleBufferLoading);
    $('#manualControl-unloadBufferButton').on('click', handle_button_sampleBufferUnloading);

    // Ender3 Control
    $('#ender3-moveToSampleButton').on('click', handle_button_moveToSample);
    $('#ender3-moveToRestButton').on('click', handle_button_moveToRest);
    $('#ender3-moveToHomeButton').on('click', handle_button_moveToHome);
    $('#ender3-moveToStageButton').on('click', handle_button_moveToStage);
    $('#ender3-moveEjectBedButton').on('click', handle_button_moveEjectBed);
    $('#ender3-homeButton').on('click', handle_button_homeEnder3);

    // Arduino Control
    $('#arduino-gripper-open').on('click', handle_button_arduinoGripperOpen);
    $('#arduino-gripper-close').on('click', handle_button_arduinoGripperClose);
    $('#arduino-linrail-move-up').on('click', handle_button_arduinoLinrailMoveUp);
    $('#arduino-linrail-move-down').on('click', handle_button_arduinoLinrailMoveDown);
    $('#arduino-linrail-home').on('click', handle_button_arduinoLinrailHome);

    // Enable Heating Section
    // Toggle visibility of the temperature inputs and estimated time when checkbox is checked
    $('#enable-temperature').on('change', function() {
        const temperatureInputs = $('#temperature-inputs');
        const estimatedTime = $('#estimated-time');
        
        if ($(this).is(':checked')) {
            temperatureInputs.show();
            estimatedTime.show();
            displayProcedureTime(); // Update time when section is shown
        } else {
            temperatureInputs.hide();
            estimatedTime.hide(); // Hide the estimated time
        }
    });
    // Add event listeners to update the estimated time when relevant fields change
    $('#min-angle, #max-angle, #precision-select, #min-temperature, #max-temperature, #number-of-scans').on('input', displayProcedureTime);

});

//////////////////////////////////////////////
// Queue Management

// Function to render the queue items in the sortable list
function renderQueue() {
    queueList.innerHTML = ''; // Clear the list before rendering

    // For each of the items in the queue list, make a queue item and add it to the sortable list
    queueItems_array.forEach((item, index) => {

        // Construct the text for the temperatures
        const estTime_min = calculateProcedureTime(Math.min(...item.temperatures), Math.max(...item.temperatures), 
                                                    item.minAngle, item.maxAngle, item.precision, 
                                                    item.temperatures.length).totalTime;
        const temperaturesText = item.temperatures.length ? 
                `${Math.min(...item.temperatures)}°C - ${Math.max(...item.temperatures)}°C, ${item.temperatures.length} Scans (approx. ${(estTime_min/60).toFixed(2)} hrs)` 
                : 'No heating';

        // Create the list item
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        listItem.innerHTML = `
                <div class="flex-grow-1">
                    <span class="item-name" style="display: block;">${item.itemName}</span>
                    <span class="item-details" style="display: block;">Sample Number: ${item.sampleNumber} </span>
                    <span class="item-details" style="display: block;">2θ = ${item.minAngle}° - ${item.maxAngle}°, Precision: ${item.precision}</span>
                    <span class="item-details" style="display: block;">Temperature: ${temperaturesText} </span>
                </div>
            `;

        // Create delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-danger btn-sm';
        deleteButton.textContent = 'X';
        deleteButton.onclick = function () {
            queueItems_array.splice(index, 1); // Remove item from queue
            renderQueue(); // Re-render the queue
        };

        listItem.appendChild(deleteButton);
        queueList.appendChild(listItem);
    });
}

// Function to display currently running item
function renderCurrentlyRunning(systemStateData) {
    const runningItemDiv = document.getElementById('running-item');

    if (queueRunningItem == null) {
        runningItemDiv.innerHTML = '';
        return;
    }

    // Construct the text for the temperatures
    const estTime_min = calculateProcedureTime(Math.min(...queueRunningItem.temperatures), Math.max(...queueRunningItem.temperatures), 
                        queueRunningItem.minAngle, queueRunningItem.maxAngle, queueRunningItem.precision, 
                        queueRunningItem.temperatures.length).totalTime;
    const temperaturesText = queueRunningItem.temperatures.length ? 
        `${Math.min(...queueRunningItem.temperatures)}°C - ${Math.max(...queueRunningItem.temperatures)}°C, ${queueRunningItem.temperatures.length} Scans (approx. ${(estTime_min/60).toFixed(2)} hrs)` 
        : 'No heating';

    runningItemDiv.innerHTML = `
            <div class="flex-grow-1">
                <span class="item-name" style="display: block;">${queueRunningItem.itemName}</span>
                <span class="item-details" style="display: block;">Sample Number: ${queueRunningItem.sampleNumber} </span>
                <span class="item-details" style="display: block;">2θ = ${queueRunningItem.minAngle}° - ${queueRunningItem.maxAngle}°, Precision: ${queueRunningItem.precision}</span>
                <span class="item-details" style="display: block;">Temperature: ${temperaturesText} </span>
            </div>
    `;// Display in Currently Running box
}


// Function to handle adding a new item to the queue
function handle_button_queueAdd(event) {
    event.preventDefault();

    // Get basic fields
    const itemName = $.trim(itemNameInput.value);  // Assuming itemNameInput is defined elsewhere
    const sampleNumber = $('input[name="sample-number"]:checked');

    // Validate itemName and sampleNumber
    if (!itemName || !sampleNumber.length) {
        alert('Please fill out all fields.');
        return;
    }

    // Get the new fields
    const minAngle = parseFloat($('#min-angle').val());
    const maxAngle = parseFloat($('#max-angle').val());
    const precision = $('#precision-select').val();

    let temperatures = [];
    if ($('#enable-temperature').is(':checked')) {
        const minTemp = parseFloat($('#min-temperature').val());
        const maxTemp = parseFloat($('#max-temperature').val());
        const numScans = parseInt($('#number-of-scans').val());

        // Validate temperature fields
        if (isNaN(minTemp) || isNaN(maxTemp) || isNaN(numScans)) {
            alert('Please fill out all temperature fields.');
            return;
        }

        // Linear interpolation of temperatures
        const tempStep = (maxTemp - minTemp) / (numScans - 1);
        temperatures = Array.from({ length: numScans }, (_, i) => minTemp + i * tempStep);
    }

    // Construct the new item object
    const newItem = {
        itemName: itemName,
        sampleNumber: sampleNumber.val(),
        minAngle: minAngle,
        maxAngle: maxAngle,
        precision: precision,
        temperatures: temperatures
    };

    // Add new item to the queue
    queueItems_array.push(newItem);
    renderQueue(); // Render the updated queue

    // Clear the input fields
    itemNameInput.value = '';
    $('#min-angle').val(10); // Reset to default value (adjust as needed)
    $('#max-angle').val(80); // Reset to default value (adjust as needed)
    $('#precision-select').val('Low'); // Reset to default value
    
    $('#min-temperature').val(25); // Reset default temperature
    $('#max-temperature').val(''); // Clear the max temperature
    $('#number-of-scans').val(200); // Reset to default value
    $('#estimated-time').text(''); // Hide estimated time
    $('#time-breakdown').hide(); // Hide estimated time

    // Uncheck the current sample number and check the next one
    sampleNumber.prop('checked', false);
    const nextSample = $(`input[name="sample-number"][value="${parseInt(sampleNumber.val()) + 1}"]`);
    
    // If the next sample exists, check it; otherwise, check the first sample again
    if (nextSample.length) {
        nextSample.prop('checked', true);
    } else {
        $('input[name="sample-number"][value="0"]').prop('checked', true);
    }
}

// Function to send the next item in the queue as a command, and remove it from the queue
function sendNextQueueItem() {
    //This is when the queue is empty
    if (queueItems_array.length === 0) {
        console.log('Queue is empty.');
        queue_paused = true;
        queueRunningItem = null;    // Clear the running item
        return;
    }

    queueRunningItem = queueItems_array.shift(); // Remove the first item from the queue
    renderQueue(); // Re-render the queue to reflect changes

    const command_package = {
        sample_name: queueRunningItem.itemName,
        sample_num: queueRunningItem.sampleNumber,
        xrd_params: {
            min_angle: queueRunningItem.minAngle,
            max_angle: queueRunningItem.maxAngle,
            precision: queueRunningItem.precision,
            temperatures: queueRunningItem.temperatures
        }
    }

    // Send the command to the Flask endpoint
    $.ajax({
        url: '/api/command',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(command_package),
        success: function (data) {
            console.log('Command Response: ', data);
        }
    });
}

function handle_button_queueStart() {

    if (queueItems_array.length > 0) {
        queue_paused = false;
        sendNextQueueItem();
    } else {
        alert('No items in the queue to start.');
    }
}

function handle_button_queuePause() {
    queue_paused = true;    // Set the queue to paused, so it doesn't send the next item
}

function handle_button_queueAbort() {
    queue_paused = true;    // Set the queue to paused, so it doesn't send the next item

    // Send the abort command to the Flask endpoint
    $.ajax({
        url: '/api/abort',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Abort Response: ', data);
        }
    });
}

//////////////////////////////////////////////
// Manual Control (AISH Sample Loader)

// Manual Loading
function handle_button_manualLoading(event) {
    event.preventDefault();
    console.log('Load button clicked');

    // Get the selected radio button value from the specific container
    const sampleNumber = $('#manualControl-samplePos input[name="sample-number"]:checked').val();
    
    $.ajax({
        url: '/api/load_sample',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ sample_num: sampleNumber }),  // Send sample number in JSON
        success: function (data) {
            console.log('Load Button Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error: ', error);
        }
    });
}

// Manual Unloading
function handle_button_manualUnloading(event) {
    event.preventDefault();
    $.ajax({
        url: '/api/unload_sample',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Unload Button Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error: ', error);
        }
    });
}

//Sample buffer loading
function handle_button_sampleBufferLoading(event) {
    event.preventDefault();
    console.log('Sample Buffer Load button clicked');
    
    $.ajax({
        url: '/api/loading_sample_buffer',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Sample Buffer Load Button Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error: ', error);
        }
    });
}

//Sample buffer unloading
function handle_button_sampleBufferUnloading(event) {
    event.preventDefault();
    console.log('Sample Buffer Unload button clicked');
    
    $.ajax({
        url: '/api/done_loading_sample_buffer',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Sample Buffer Unload Button Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error: ', error);
        }
    });
}



//////////////////////////////////////////////
// Ender3 Control

function handle_button_moveToSample(event) {
    event.preventDefault();
    
    // Get the selected radio button value from the specific container
    const sampleNumber = $('#ender3-sampleNumber-container input[name="sample-number"]:checked').val();
    
    console.log('Move to Sample: ', sampleNumber);

    $.ajax({
        url: '/api/ender3/move_to_sample',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ sample_num: sampleNumber }),
        success: function (data) {
            console.log('Move to Sample Response: ', data);
        }
    });
}

function handle_button_moveToRest(event) {
    event.preventDefault();
    console.log('Move to Rest Position');

    $.ajax({
        url: '/api/ender3/move_to_rest',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Move to Rest Response: ', data);
        }
    });
}

function handle_button_moveToHome(event) {
    event.preventDefault();
    console.log('Move to Home Position');

    $.ajax({
        url: '/api/ender3/move_to_home',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Move to Home Response: ', data);
        }
    });
}

function handle_button_moveToStage(event) {
    event.preventDefault();
    console.log('Move to Stage Position');

    $.ajax({
        url: '/api/ender3/move_to_stage',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Move to Stage Response: ', data);
        }
    });
}

function handle_button_moveEjectBed(event) {
    event.preventDefault();
    console.log('Eject Bed');

    $.ajax({
        url: '/api/ender3/move_eject_bed',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Eject Bed Response: ', data);
        }
    });
}

function handle_button_homeEnder3(event) {
    event.preventDefault();
    console.log('Home Ender3');

    $.ajax({
        url: '/api/ender3/home',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Home Ender3 Response: ', data);
        }
    });
}

//////////////////////////////////////////////
// Arduino Control

// Callback function to open the Arduino gripper
function handle_button_arduinoGripperOpen(event) {
    event.preventDefault();
    console.log('Arduino Gripper Open button clicked');
    
    $.ajax({
        url: '/api/arduino/gripper/open',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Gripper Open Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error opening gripper: ', error);
        }
    });
}

// Callback function to close the Arduino gripper
function handle_button_arduinoGripperClose(event) {
    event.preventDefault();
    console.log('Arduino Gripper Close button clicked');
    
    $.ajax({
        url: '/api/arduino/gripper/close',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Gripper Close Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error closing gripper: ', error);
        }
    });
}

// Callback function to move the Arduino linear rail up
function handle_button_arduinoLinrailMoveUp(event) {
    event.preventDefault();
    console.log('Arduino Linear Rail Move Up button clicked');
    
    $.ajax({
        url: '/api/arduino/linear_rail/move_up',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Linear Rail Move Up Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error moving linear rail up: ', error);
        }
    });
}

// Callback function to move the Arduino linear rail down
function handle_button_arduinoLinrailMoveDown(event) {
    event.preventDefault();
    console.log('Arduino Linear Rail Move Down button clicked');
    
    $.ajax({
        url: '/api/arduino/linear_rail/move_down',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Linear Rail Move Down Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error moving linear rail down: ', error);
        }
    });
}

// Callback function to home the Arduino linear rail
function handle_button_arduinoLinrailHome(event) {
    event.preventDefault();
    console.log('Arduino Linear Rail Home button clicked');
    
    $.ajax({
        url: '/api/arduino/linear_rail/home',
        method: 'POST',
        contentType: 'application/json',
        success: function (data) {
            console.log('Linear Rail Home Response: ', data);
        },
        error: function (xhr, status, error) {
            console.error('Error homing linear rail: ', error);
        }
    });
}
