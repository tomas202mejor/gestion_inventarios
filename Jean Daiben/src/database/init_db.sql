
-- ======================================
-- SCRIPT 1 COMPLETO DEL PROYECTO JEAN DAIBEN - MYSQL
-- ======================================

-- TABLAS
CREATE TABLE Usuarios (
    UsuarioID INT PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    ContrasenaHash VARCHAR(255) NOT NULL
);

CREATE TABLE Productos (
    ProductoID INT PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(100) NOT NULL,
    Cantidad INT NOT NULL,
    Tipo VARCHAR(50),
    Proveedor VARCHAR(100)
);

CREATE TABLE Clientes (
    ClienteID INT PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(100) NOT NULL,
    TipoCliente VARCHAR(50) NOT NULL
);

CREATE TABLE Ventas (
    VentaID INT PRIMARY KEY AUTO_INCREMENT,
    ClienteID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT NOW(),
    TotalVenta DECIMAL(10, 2),
    MetodoPago VARCHAR(50),
    FOREIGN KEY (ClienteID) REFERENCES Clientes(ClienteID)
);

CREATE TABLE DetalleVentas (
    DetalleVentaID INT PRIMARY KEY AUTO_INCREMENT,
    VentaID INT NOT NULL,
    ProductoID INT NOT NULL,
    Cantidad INT NOT NULL,
    PrecioUnitario DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
);

CREATE TABLE Facturas (
    FacturaID INT PRIMARY KEY AUTO_INCREMENT,
    VentaID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT NOW(),
    Total DECIMAL(10,2),
    Estado VARCHAR(50),
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID)
);

CREATE TABLE Alertas (
    AlertaID INT PRIMARY KEY AUTO_INCREMENT,
    ProductoID INT NOT NULL,
    NivelBajo INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT NOW(),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
);

-- TRIGGER
DELIMITER $$

CREATE TRIGGER AlertaStockBajo
AFTER UPDATE ON Productos
FOR EACH ROW
BEGIN
    IF NEW.Cantidad < 10 THEN
        INSERT INTO Alertas (ProductoID, NivelBajo)
        VALUES (NEW.ProductoID, NEW.Cantidad);
    END IF;
END$$

DELIMITER ;

-- PROCEDIMIENTO: REGISTRAR VENTA
DELIMITER $$

CREATE PROCEDURE RegistrarVenta(
    IN p_ClienteID INT,
    IN p_MetodoPago VARCHAR(50)
)
BEGIN
    DECLARE v_VentaID INT;
    DECLARE v_TotalVenta DECIMAL(10,2) DEFAULT 0;

    -- Crear una venta temporal sin total
    INSERT INTO Ventas (ClienteID, Fecha, MetodoPago)
    VALUES (p_ClienteID, NOW(), p_MetodoPago);

    SET v_VentaID = LAST_INSERT_ID();

    -- En MySQL no se pueden pasar tablas directamente, así que esto debe manejarse desde el código de aplicación

    -- Aquí irían los inserts a DetalleVentas desde la app, luego...

    -- Calcular total
    SELECT SUM(Cantidad * PrecioUnitario) INTO v_TotalVenta
    FROM DetalleVentas
    WHERE VentaID = v_VentaID;

    -- Actualizar total de venta
    UPDATE Ventas SET TotalVenta = v_TotalVenta WHERE VentaID = v_VentaID;

    -- Insertar Factura
    INSERT INTO Facturas (VentaID, Fecha, Total, Estado)
    VALUES (v_VentaID, NOW(), v_TotalVenta, 'Pendiente');
END$$

DELIMITER ;

-- PROCEDIMIENTO: REPORTE VENTAS POR PERIODO
DELIMITER $$

CREATE PROCEDURE ReporteVentasPorPeriodo(
    IN p_FechaInicio DATE,
    IN p_FechaFin DATE
)
BEGIN
    SELECT V.VentaID, C.Nombre AS Cliente, V.Fecha, V.TotalVenta, V.MetodoPago
    FROM Ventas V
    INNER JOIN Clientes C ON V.ClienteID = C.ClienteID
    WHERE V.Fecha BETWEEN p_FechaInicio AND p_FechaFin;
END$$

DELIMITER ;

-- PROCEDIMIENTO: REPORTE STOCK DISPONIBLE
DELIMITER $$

CREATE PROCEDURE ReporteStockDisponible()
BEGIN
    SELECT ProductoID, Nombre, Cantidad AS CantidadDisponible
    FROM Productos;
END$$

DELIMITER ;


-- ======================================
-- AGREGADO PARA MÓDULO DE PEDIDOS - SPRINT 2
-- ======================================

-- TABLA: Pedidos
CREATE TABLE Pedidos (
    PedidoID INT PRIMARY KEY AUTO_INCREMENT,
    ClienteID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT NOW(),
    Estado VARCHAR(50) DEFAULT 'Pendiente',
    Observaciones TEXT,
    FOREIGN KEY (ClienteID) REFERENCES Clientes(ClienteID)
);

-- TABLA: DetallePedidos
CREATE TABLE DetallePedidos (
    DetallePedidoID INT PRIMARY KEY AUTO_INCREMENT,
    PedidoID INT NOT NULL,
    ProductoID INT NOT NULL,
    Cantidad INT NOT NULL,
    PrecioUnitario DECIMAL(10,2),
    FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
);

-- PROCEDIMIENTO: Registrar un nuevo pedido
DELIMITER $$

CREATE PROCEDURE RegistrarPedido(
    IN p_ClienteID INT,
    IN p_Observaciones TEXT
)
BEGIN
    INSERT INTO Pedidos (ClienteID, Fecha, Estado, Observaciones)
    VALUES (p_ClienteID, NOW(), 'Pendiente', p_Observaciones);
END$$

DELIMITER ;

-- PROCEDIMIENTO: Marcar pedido como completado
DELIMITER $$

CREATE PROCEDURE CompletarPedido(
    IN p_PedidoID INT
)
BEGIN
    UPDATE Pedidos
    SET Estado = 'Completado'
    WHERE PedidoID = p_PedidoID;
END$$

DELIMITER ;

-- PROCEDIMIENTO: Consultar pedidos por estado
DELIMITER $$

CREATE PROCEDURE ConsultarPedidosPorEstado(
    IN p_Estado VARCHAR(50)
)
BEGIN
    SELECT P.PedidoID, C.Nombre AS Cliente, P.Fecha, P.Estado, P.Observaciones
    FROM Pedidos P
    INNER JOIN Clientes C ON P.ClienteID = C.ClienteID
    WHERE P.Estado = p_Estado;
END$$

DELIMITER ;