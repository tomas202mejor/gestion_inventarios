
-- ======================================
-- SCRIPT COMPLETO DEL PROYECTO JEAN DAIBEN
-- ======================================

-- TABLAS
CREATE TABLE Usuarios (
    UsuarioID INT PRIMARY KEY IDENTITY,
    Nombre NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100) NOT NULL UNIQUE,
    ContrasenaHash NVARCHAR(255) NOT NULL
);

CREATE TABLE Productos (
    ProductoID INT PRIMARY KEY IDENTITY,
    Nombre NVARCHAR(100) NOT NULL,
    Cantidad INT NOT NULL,
    Tipo NVARCHAR(50),
    Proveedor NVARCHAR(100)
);

CREATE TABLE Clientes (
    ClienteID INT PRIMARY KEY IDENTITY,
    Nombre NVARCHAR(100) NOT NULL,
    TipoCliente NVARCHAR(50) NOT NULL
);

CREATE TABLE Ventas (
    VentaID INT PRIMARY KEY IDENTITY,
    ClienteID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT GETDATE(),
    TotalVenta DECIMAL(10, 2),
    MetodoPago NVARCHAR(50),
    FOREIGN KEY (ClienteID) REFERENCES Clientes(ClienteID)
);

CREATE TABLE DetalleVentas (
    DetalleVentaID INT PRIMARY KEY IDENTITY,
    VentaID INT NOT NULL,
    ProductoID INT NOT NULL,
    Cantidad INT NOT NULL,
    PrecioUnitario DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
);

CREATE TABLE Facturas (
    FacturaID INT PRIMARY KEY IDENTITY,
    VentaID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT GETDATE(),
    Total DECIMAL(10,2),
    Estado NVARCHAR(50),
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID)
);

CREATE TABLE Alertas (
    AlertaID INT PRIMARY KEY IDENTITY,
    ProductoID INT NOT NULL,
    NivelBajo INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
);

-- TRIGGER
CREATE TRIGGER AlertaStockBajo
ON Productos
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO Alertas (ProductoID, NivelBajo)
    SELECT i.ProductoID, i.Cantidad
    FROM inserted i
    WHERE i.Cantidad < 10;
END;

-- PROCEDIMIENTO: REGISTRAR VENTA
CREATE PROCEDURE RegistrarVenta
    @ClienteID INT,
    @MetodoPago NVARCHAR(50),
    @DetalleProductos TABLE (
        ProductoID INT,
        Cantidad INT,
        PrecioUnitario DECIMAL(10, 2)
    )
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @VentaID INT;
    DECLARE @TotalVenta DECIMAL(10,2);

    SELECT @TotalVenta = SUM(Cantidad * PrecioUnitario)
    FROM @DetalleProductos;

    INSERT INTO Ventas (ClienteID, Fecha, TotalVenta, MetodoPago)
    VALUES (@ClienteID, GETDATE(), @TotalVenta, @MetodoPago);

    SET @VentaID = SCOPE_IDENTITY();

    INSERT INTO DetalleVentas (VentaID, ProductoID, Cantidad, PrecioUnitario)
    SELECT @VentaID, ProductoID, Cantidad, PrecioUnitario
    FROM @DetalleProductos;

    UPDATE p
    SET p.Cantidad = p.Cantidad - dp.Cantidad
    FROM Productos p
    INNER JOIN @DetalleProductos dp ON p.ProductoID = dp.ProductoID;

    INSERT INTO Facturas (VentaID, Fecha, Total, Estado)
    VALUES (@VentaID, GETDATE(), @TotalVenta, 'Pendiente');
END;

-- PROCEDIMIENTO: REPORTE VENTAS POR PERIODO
CREATE PROCEDURE ReporteVentasPorPeriodo
    @FechaInicio DATE,
    @FechaFin DATE
AS
BEGIN
    SELECT V.VentaID, C.Nombre AS Cliente, V.Fecha, V.TotalVenta, V.MetodoPago
    FROM Ventas V
    INNER JOIN Clientes C ON V.ClienteID = C.ClienteID
    WHERE V.Fecha BETWEEN @FechaInicio AND @FechaFin;
END;

-- PROCEDIMIENTO: REPORTE STOCK DISPONIBLE
CREATE PROCEDURE ReporteStockDisponible
AS
BEGIN
    SELECT ProductoID, Nombre, Cantidad AS CantidadDisponible
    FROM Productos;
END;
