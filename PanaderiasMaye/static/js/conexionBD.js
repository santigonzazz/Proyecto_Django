let mysql = require("mysql");

let conexion = mysql.createConnection({
    host: "localhost",
    database: "panaderiasmaye",
    user: "root",
    password: ""
})

conexion.connect(function(err){
    if(err){
        throw err;
    }else{
        console.log("Todo piola")
    }
})

conexion.end()