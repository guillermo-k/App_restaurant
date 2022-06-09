

function desplegar(id) {
    var x = document.getElementById(id);
    if (x.style.display === "none") {
        document.getElementById("agregarUsuario").style.display = "none";
        document.getElementById("editarUsuario").style.display = "none";
        document.getElementById("editarPlatos").style.display = "none";
        document.getElementById("editarCategoria").style.display = "none";
        document.getElementById("cantidadMesas").style.display = "none";
        
        x.style.display = "block";
    } else {
        document.getElementById("agregarPlato").style.display = "none";
        x.style.display = "none";
    }
}

function ver(id) {
    console.log(id);
    var x = document.getElementById(id);
    var y = document.getElementsByClassName(id)
    if (x.style.display === "none") {
        x.style.display = "block";
        y[0].innerHTML="Ocultar"
    } else {
        x.style.display = "none";
        y[0].innerHTML="Ver"
    }
}

function cambiar(id,id2) {
    var x = document.getElementById(id);
    var y = document.getElementById(id2);
    if (x.style.display === "none") {
        x.style.display = "block";
        y.style.display = "none";
    } else {
        y.style.display = "block";
        x.style.display = "none";
    }
}