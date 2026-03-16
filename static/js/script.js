let fecha = new Date("Apr 11, 2026 22:00:00").getTime();

let x = setInterval(function(){

let ahora = new Date().getTime();

let distancia = fecha - ahora;

let dias = Math.floor(distancia / (1000*60*60*24));
let horas = Math.floor((distancia % (1000*60*60*24)) / (1000*60*60));
let minutos = Math.floor((distancia % (1000*60*60)) / (1000*60));

document.getElementById("countdown").innerHTML =
dias + " días " + horas + " horas " + minutos + " minutos";

},1000);