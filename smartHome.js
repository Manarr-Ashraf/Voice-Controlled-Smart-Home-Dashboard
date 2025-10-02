// ---------- Mosquitto -----------------
const clientId = 'web-dashboard-' + Math.floor((Math.random() * 100000) + 1);
const client = mqtt.connect('ws://192.168.1.3:9001', { 
    clientId,
    protocolVersion: 4,
    clean: true,
    keepalive: 60
});

//---------- Topics status ---------------
const DOOR_STATUS = "esp/door/status";
const LIGHT_STATUS = "esp/light/status";
const PERSON_STATUS = "esp/person/status";
const CLIMATE_STATUS = "esp/climate/status";

//---------- Topics commands --------------
const DOOR_COMMAND = "esp/door/command";
const LIGHT_COMMAND = "esp/light/command";
const PERSON_COMMAND = "esp/person/command";
const CLIMATE_COMMAND = "esp/climate/command";

client.on('connect', function () {
    console.log("Connected to Mosquitto");
    
    client.subscribe([DOOR_STATUS, LIGHT_STATUS, PERSON_STATUS, CLIMATE_STATUS], (err) => {
        if (!err) {
            console.log("Subscribed to status topics");
        }
    });
});


client.on('message', function (topic, message) {
    const data = JSON.parse(message.toString());

    if (topic === DOOR_STATUS) {
        const doorImg = document.querySelector('.door img');
        const doorText = document.querySelector('.door h2');
        doorImg.src = data.door === "opened" ? "/assets/openedDoor.png" : "/assets/closeDoor.png";
        doorText.textContent = data.door === "opened" ? "Opened" : "Closed";
    }

    if (topic === LIGHT_STATUS) {
        const lightImg = document.querySelector('.light img');
        const lightText = document.querySelector('.light h2');
        lightImg.src = data.light === "light on" ? "/assets/lightOn.png" : "/assets/lightOff.png";
        lightText.textContent = data.light === "light on" ? "Light On" : "Light Off";
    }

    if (topic === PERSON_STATUS) {
        const personImg = document.querySelector('.person img');
        const personText = document.querySelector('.person h2');
        personImg.src = data.person === "someone" ? "/assets/Person3.png" : "/assets/noPerson.png";
        personText.textContent = data.person === "someone" ? "Someone is there" : "No one is there";
    }

    if (topic === CLIMATE_STATUS) {
        if (data.temperature) {
            document.querySelector('.temp h2').textContent = `${data.temperature}°C`;
        }
        if (data.humidity) {
            document.querySelector('.humi h2').textContent = `${data.humidity}%`;
        }
    }
});


//--------------------------------- dashboard ------------------------------------------
//door
document.querySelector('.dashboard .Dcontainer').addEventListener('click', function () {
    const isOpen = document.querySelector('.door h2').textContent === "Opened";
    client.publish(DOOR_COMMAND, JSON.stringify({ command: isOpen ? "close" : "open" }));
});

//light
document.querySelector('.dashboard .Lcontainer').addEventListener('click', function () {
    const isOn = document.querySelector('.light h2').textContent === "Light On";
    client.publish(LIGHT_COMMAND, JSON.stringify({ command: isOn ? "turn off" : "turn on" }));
});

