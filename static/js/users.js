const usuariosTable = document.querySelector("table");
const usuarioForm = document.getElementById("usuarioForm");
const nombreInput = document.getElementById("nombre");
const apellidoInput = document.getElementById("apellido");
const telefonoInput = document.getElementById("telefono");
const correoInput = document.getElementById("correo");
const usuarioInput = document.getElementById("usuario");
const tipoUsuarioSelect = document.getElementById("tipoUsuario");
const fechaNacimientoInput = document.getElementById("fechaNacimiento");
let idUser = false;

function cargarUsuarios() {
  fetch("/api/usuarios")
    .then((response) => response.json())
    .then((usuarios) => {
      console.log("Usuarios:", usuarios);
      const tbody = document.querySelector("#usuariosTable tbody");
      tbody.innerHTML = "";
      usuarios.forEach((usuario) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
                <td>${usuario.id}</td>
                <td>${usuario.nombre}</td>
                <td>${usuario.apellido}</td>
                <td>${usuario.telefono}</td>
                <td>${usuario.correo_electronico}</td>
                <td>${usuario.usuario}</td>
                <td>${(x = usuario.fk_tipo_usuario == 1 ? "Administrador" : "Invitado")}</td>
                <td>${new Date(usuario.fecha_nacimiento).toLocaleDateString()}</td>
                <td>
                    <button onclick="editarUsuario(${usuario.id})">Editar</button>
                    <button onclick="eliminarUsuario(${usuario.id})">Eliminar</button>
                </td>
            `;
        tbody.appendChild(tr);
      });
    })
    .catch((error) => console.error("Error al obtener usuarios:", error));
}

function eliminarUsuario(id) {
  fetch(`/api/usuarios/${id}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      alert("Registro Eliminado Correctamente");
      window.location.reload();
    })
    .catch((error) => console.error("Error al eliminar usuario:", error));
}

function editarUsuario(id) {
  fetch(`/api/usuarios/${id}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Usuario no encontrado");
      }
      return response.json();
    })
    .then((usuario) => {
      idUser = id;
      nombreInput.value = usuario.nombre;
      apellidoInput.value = usuario.apellido;
      telefonoInput.value = usuario.telefono;
      correoInput.value = usuario.correo_electronico;
      usuarioInput.value = usuario.usuario;
      tipoUsuarioSelect.value = usuario.fk_tipo_usuario.toString();
      fechaNacimientoInput.value = new Date(usuario.fecha_nacimiento).toISOString().slice(0, 16);
    })
    .catch((error) => console.error("Error al obtener usuario por ID:", error));
}

document.addEventListener("DOMContentLoaded", function () {
  cargarUsuarios();
});

usuarioForm.addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(usuarioForm);
  const datosEnviar = {
    id: idUser,
    nombre: formData.get("nombre"),
    apellido: formData.get("apellido"),
    telefono: formData.get("telefono"),
    correo_electronico: formData.get("correo"),
    usuario: formData.get("usuario"),
    fk_tipo_usuario: formData.get("tipoUsuario"),
    fecha_nacimiento: formData.get("fechaNacimiento"),
    pwd: formData.get("pwd"),
  };

  console.log(datosEnviar);

  if (idUser > 0) {
    fetch(`/api/usuarios/${idUser}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(datosEnviar),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Usuario actualizado:", data);
        idUser = 0;
        window.location.reload();
      })
      .catch((error) => console.error("Error al actualizar usuario:", error));
  } else {
    fetch("/api/usuarios", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(datosEnviar),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Usuario creado:", data);
        idUser = 0;
        window.location.reload();
      })
      .catch((error) => console.error("Error al crear usuario:", error));
  }
});
