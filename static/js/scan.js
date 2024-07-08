const socket = io();
const cameraSelect = document.getElementById("camera-select");
const video = document.getElementById("video");
const canvas = document.createElement("canvas");
const context = canvas.getContext("2d");
const processed = document.getElementById("processed");
let base64String = '';
let fruitStates;
let port;
let writer;
let reader;
let flashState = false;

canvas.width = video.width;
canvas.height = video.height;

async function startCamera(deviceId) {
  const constraints = {
    video: {
      deviceId: deviceId ? { exact: deviceId } : undefined,
    },
  };
  const stream = await navigator.mediaDevices.getUserMedia(constraints);

  video.srcObject = stream;
  video.play();

  socket.on("processed_frame", function (data) {
    processed.src = data;
    base64String = data;
    document.querySelector(".loading-screen").style.display = "none";
    console.log("Processed....");
  });

  socket.on("processed_data", function (json_data) {
    console.log(json_data);
    fruitStates = JSON.parse(json_data);
    prepareTables(fruitStates);
  });
}

async function saveScan() {
  if (Object.keys(fruitStates).length > 0) {
    try {
      if (!base64String) {
        alert("No se ha recibido una imagen procesada.");
        return;
      }

      const payload = {
        fruitStates,
        image: base64String,
      };

      const url = "/guardar_transacciones";
      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      };

      const response = await fetch(url, requestOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const responseData = await response.json();
      console.log("Respuesta del servidor:", responseData);
      fruitStates = {};
      prepareTables(fruitStates);
    } catch (error) {
      console.error("Error al enviar los datos:", error);
    }
  } else {
    alert("Procese las frutas primero...");
  }
}

async function cancelScan() {
  console.log(fruitStates);
  fruitStates = {};
  prepareTables(fruitStates);
}

function prepareTables(fruitStates) {
  const tableBody = document.querySelector("#fruits-table tbody");
  tableBody.innerHTML = "";

  Object.keys(fruitStates).forEach((fruit) => {
    Object.keys(fruitStates[fruit]).forEach((state) => {
      const quantity = fruitStates[fruit][state];
      if (quantity > 0) {
        const row = `
          <tr>
            <td>${fruit}</td>
            <td>${state}</td>
            <td>${quantity}</td>
          </tr>
        `;
        tableBody.innerHTML += row;
      }
    });
  });
}

async function getCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  const videoDevices = devices.filter((device) => device.kind === "videoinput");
  videoDevices.forEach((device, index) => {
    const option = document.createElement("option");
    option.value = device.deviceId;
    option.text = device.label || `Camera ${index + 1}`;
    cameraSelect.appendChild(option);
  });

  cameraSelect.onchange = () => {
    const selectedDeviceId = cameraSelect.value;
    startCamera(selectedDeviceId);
  };
}

function processImage() {
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  const base64data = canvas.toDataURL("image/jpeg");
  socket.emit("video_frame", base64data);
  document.querySelector(".loading-screen").style.display = "flex";
  console.log("Processing....");
}

async function connectSerial() {
  try {
    port = await navigator.serial.requestPort();
    await port.open({ baudRate: 115200 });

    const encoder = new TextEncoderStream();
    const outputDone = encoder.readable.pipeTo(port.writable);
    writer = encoder.writable.getWriter();

    const decoder = new TextDecoderStream();
    const inputDone = port.readable.pipeTo(decoder.writable);
    reader = decoder.readable.getReader();

    readLoop();
  } catch (error) {
    console.error("Error connecting to serial port: ", error);
  }
}

async function readLoop() {
  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    document.getElementById("output").innerText += value;
  }
}

async function sendCommand(command) {
  if (writer) {
    await writer.write(command + "\n");
  } else {
    console.error("Serial port is not open.");
  }
}

document.getElementById("toggleButton").addEventListener("click", async () => {
  if (!port) {
    await connectSerial();
  }

  flashState = !flashState;
  if (flashState) {
    sendCommand("turn_on_flash");
    document.getElementById("toggleButton").innerText = "Turn Off Flash";
  } else {
    sendCommand("turn_off_flash");
    document.getElementById("toggleButton").innerText = "Turn On Flash";
  }
});
window.onload = () => {
  startCamera();
  getCameras();
};
