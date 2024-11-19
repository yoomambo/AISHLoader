const queueList = document.getElementById('queue-list');
const queueForm = document.getElementById('queue-form');
const itemNameInput = document.getElementById('item-name');
const sampleNumberInput = document.getElementById('sample-number');
const runningItemDiv = document.getElementById('running-item');
const startButton = document.getElementById('queue-start-button');

// Array to hold the queue items
let queueItems_array = [];

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


});

// Function to render the queue items in the sortable list
function renderQueue() {
    queueList.innerHTML = ''; // Clear the list before rendering

    // For each of the items in the queue list, make a queue item and add it to the sortable list
    queueItems_array.forEach((item, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        listItem.innerHTML = `
                <div class="flex-grow-1">
                    <span class="item-name">${item.itemName}</span><br>
                    <span class="item-details">Sample Number: ${item.sampleNumber} ${item.optionsText}</span>
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

function handle_button_queueAdd(event) {
    event.preventDefault();

    const itemName = $.trim(itemNameInput.value);
    const sampleNumber = $('input[name="sample-number"]:checked');
    const selectedOptions = $('input[name="options"]:checked').map(function () {
        return this.value;
    }).get();

    if (!itemName || !sampleNumber.length) {
        alert('Please fill out all fields.');
        return;
    }

    const optionsText = selectedOptions.length ? `Options: ${selectedOptions.join(', ')}` : '';
    const newItem = {
        itemName: itemName,
        sampleNumber: sampleNumber.val(),
        optionsText: optionsText
    };

    queueItems_array.push(newItem); // Add new item to the queue
    renderQueue(); // Render the updated queue

    // Clear the input fields
    itemNameInput.value = '';
    $('input[name="options"]:checked').prop('checked', false);

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


function handle_button_queueStart() {
    if (queueItems_array.length > 0) {
        const currentItem = queueItems_array.shift(); // Remove the first item from the queue
        runningItemDiv.innerHTML = `
            <div class="flex-grow-1">
                <span class="item-name">${currentItem.itemName}</span><br>
                <span class="item-details">Sample Number: ${currentItem.sampleNumber} ${currentItem.optionsText}</span>
            </div>
        `; // Display in Currently Running box
        renderQueue(); // Re-render the queue to reflect changes
    } else {
        alert('No items in the queue to start.');
    }
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
