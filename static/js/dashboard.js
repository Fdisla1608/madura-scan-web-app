const xLinesValues = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000];
var xBarValues = ["Banana", "Limón", "Mango", "USA", "Argentina"];

// Colores para las barras
const colores = {
  Verde: "rgba(75, 192, 192, 0.2)",
  Maduro: "rgba(255, 206, 86, 0.2)",
  Descompuesto: "rgba(255, 99, 132, 0.2)",
};

document.addEventListener("DOMContentLoaded", () => {
  const socket = io(); // Si el servidor está en una URL diferente, especifica la URL completa aquí

  socket.on("connect", () => {
    console.log("Conectado al servidor SocketIO");
    fetch("/api/data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId: 1, DateTimeStart: "20-07-2024", DateTimeEnd: "20-07-2024" }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Success:", data);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });

  socket.on("dashboard_update", (data) => {
    const frutas = ["Banana", "Limon", "Mango"];
    const categorias = ["Verde", "Maduro", "Descompuesto"];
    const colores = {
      Verde: "green",
      Maduro: "yellow",
      Descompuesto: "brown",
    };

    crearTarjetasFrutas(data);
    llenarTabla(data.registros);
    generarGrafico(data);

    const obtenerDatos = (fruta) => [
      data.frutas[fruta.toLowerCase()].verde,
      data.frutas[fruta.toLowerCase()].maduro,
      data.frutas[fruta.toLowerCase()].descompuesto,
    ];

    new Chart("barChart", {
      type: "bar",
      data: {
        labels: frutas,
        datasets: categorias.map((categoria, index) => ({
          label: categoria,
          backgroundColor: colores[categoria],
          data: frutas.map((fruta) => obtenerDatos(fruta)[index]),
        })),
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
        plugins: {
          title: {
            display: true,
            text: "Estado de Frutas: Verde, Maduro y Descompuesto",
          },
        },
      },
    });
  });

  socket.on("disconnect", () => {
    console.log("Desconectado del servidor SocketIO");
  });
});

function crearTarjetasFrutas(data) {
  const fruitsPanel = document.getElementById("fruits-panel");

  // Limpiar contenido previo si es necesario
  fruitsPanel.innerHTML = "";

  // Iterar sobre las frutas en el JSON
  Object.keys(data.frutas).forEach((fruta) => {
    const frutaData = data.frutas[fruta];

    // Crear elementos HTML para la tarjeta de fruta
    const cardDiv = document.createElement("div");
    cardDiv.classList.add("fruits-cards");

    const stateDiv = document.createElement("div");
    stateDiv.classList.add("fruits-cards-state");

    // Iterar sobre los estados de la fruta (Verde, Maduro, Descompuesto)
    Object.keys(frutaData).forEach((estado) => {
      const estadoValue = frutaData[estado];

      const stateCardDiv = document.createElement("div");
      stateCardDiv.classList.add("fruits-card-state");
      stateCardDiv.classList.add(estado.toLowerCase()); // Añadir clase de estado (green, mature, roaten)

      const stateLabel = document.createElement("div");
      stateLabel.textContent = `${estado}: ${estadoValue}`;
      stateCardDiv.appendChild(stateLabel);
      stateDiv.appendChild(stateCardDiv);
    });

    const titleDiv = document.createElement("div");
    titleDiv.classList.add("fruits-cards-title");
    titleDiv.textContent = fruta;

    cardDiv.appendChild(stateDiv);
    cardDiv.appendChild(titleDiv);
    fruitsPanel.appendChild(cardDiv);
  });
}

function llenarTabla(registros) {
  const tablaCuerpo = document.getElementById("frutasTabla").getElementsByTagName("tbody")[0];

  registros.forEach((registro) => {
    let fila = tablaCuerpo.insertRow();

    let celdaCod = fila.insertCell(0);
    celdaCod.textContent = registro.cod;

    let celdaDescripcion = fila.insertCell(1);
    celdaDescripcion.textContent = registro.Descripcion;

    let celdaFecha = fila.insertCell(2);
    celdaFecha.textContent = registro.fecha;

    let celdaAccion = fila.insertCell(3);
    let boton = document.createElement("button");
    boton.textContent = "Visualizar";
    boton.onclick = function () {
      visualizar(registro.cod);
    };
    celdaAccion.appendChild(boton);
  });
}

function agruparDatosPorFecha(registros) {
  const agrupados = {};

  registros.forEach((registro) => {
    const fecha = registro.fecha;
    const descripcion = registro.Descripcion;

    if (!agrupados[fecha]) {
      agrupados[fecha] = { banana: 0, limon: 0, mango: 0 };
    }

    const bananaMatch = descripcion.match(/banana.*?->\s*(\d+)/i);
    const limonMatch = descripcion.match(/limon.*?->\s*(\d+)/i);
    const mangoMatch = descripcion.match(/mango.*?->\s*(\d+)/i);

    agrupados[fecha].banana += bananaMatch ? parseInt(bananaMatch[1]) : 0;
    agrupados[fecha].limon += limonMatch ? parseInt(limonMatch[1]) : 0;
    agrupados[fecha].mango += mangoMatch ? parseInt(mangoMatch[1]) : 0;
  });

  return agrupados;
}

function generarGrafico(data) {
  const datosAgrupados = agruparDatosPorFecha(data.registros);

  const labels = Object.keys(datosAgrupados);
  const bananaData = labels.map((fecha) => datosAgrupados[fecha].banana);
  const limonData = labels.map((fecha) => datosAgrupados[fecha].limon);
  const mangoData = labels.map((fecha) => datosAgrupados[fecha].mango);

  new Chart("myChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Banana",
          data: bananaData,
          borderColor: "red",
          fill: false,
        },
        {
          label: "Limón",
          data: limonData,
          borderColor: "green",
          fill: false,
        },
        {
          label: "Mango",
          data: mangoData,
          borderColor: "blue",
          fill: false,
        },
      ],
    },
    options: {
      legend: { display: true },
    },
  });
}

function visualizar(cod) {
  const screen = document.getElementById("visualize-screen");
  const renderImage = document.getElementById("images-render");
  renderImage.src = `/uploads/${cod}`;
  screen.style.display = "flex";
}

function cerrarVisualizar() {
  const screen = document.getElementById("visualize-screen");
  screen.style.display = "none";
}
