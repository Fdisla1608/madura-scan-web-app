CREATE DATABASE Madura_Scan_DB;

USE Madura_Scan_DB;

CREATE TABLE
    tipo_usuario (
        id INT NOT NULL AUTO_INCREMENT,
        descripcion VARCHAR(50),
        PRIMARY KEY (id)
    );

CREATE TABLE
    estado_fruta (
        id INT NOT NULL AUTO_INCREMENT,
        descripcion VARCHAR(50),
        PRIMARY KEY (id)
    );

CREATE TABLE
    fruta (
        id INT NOT NULL AUTO_INCREMENT,
        descripcion VARCHAR(50),
        PRIMARY KEY (id)
    );

CREATE TABLE
    usuario (
        id INT NOT NULL AUTO_INCREMENT,
        fk_tipo_usuario INT NOT NULL,
        nombre VARCHAR(50) NOT NULL,
        apellido VARCHAR(50) NOT NULL,
        telefono VARCHAR(50),
        correo_electronico VARCHAR(50) NOT NULL,
        usuario VARCHAR(25) NOT NULL,
        pwd VARCHAR(200) NOT NULL,
        fecha_nacimiento DATETIME,
        fecha_registro DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (fk_tipo_usuario) REFERENCES tipo_usuario (id)
    );

CREATE TABLE
    inicio_sesion (
        id INT NOT NULL AUTO_INCREMENT,
        fk_usuario INT NOT NULL,
        fecha_registro DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (fk_usuario) REFERENCES usuario (id)
    );

CREATE TABLE
    transaccion (
        id INT NOT NULL AUTO_INCREMENT,
        fk_usuario INT NOT NULL,
        fk_fruta INT NOT NULL,
        fk_estado_fruta INT NOT NULL,
        cantidad int NOT NULL,
        fecha_registro DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (fk_usuario) REFERENCES usuario (id),
        FOREIGN KEY (fk_fruta) REFERENCES fruta (id),
        FOREIGN KEY (fk_estado_fruta) REFERENCES estado_fruta (id)
    );


INSERT INTO fruta (descripcion) values("Limon");
INSERT INTO fruta (descripcion) values("Banana");
INSERT INTO fruta (descripcion) values("Mango");

INSERT INTO estado_fruta (descripcion) values("Verde");
INSERT INTO estado_fruta (descripcion) values("Maduro");
INSERT INTO estado_fruta (descripcion) values("Descompuesto");


INSERT INTO tipo_usuario (descripcion) values("Administrador");
INSERT INTO tipo_usuario (descripcion) values("Invitado");

INSERT INTO usuario values (1,1,"SYS","Admin", "849-878-0396", "fdisla1608@gmail.com", "root","scrypt:32768:8:1$eRsclIwwjcZhxEgj$fa499124be6623255c9774d793f5ff78291c419e41b7a273f89891071d1d5475f3be27793fc708f328ddcdc4bd8113eb6b791e45105dd49b5af0571dcfbdbe20","1998-10-16",NOW());
-- user:root && pass: 1234