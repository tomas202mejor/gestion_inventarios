-- ======================================
-- ESQUEMA CORREGIDO PARA JEAN DAIBEN - MYSQL
-- ======================================

-- TABLA USUARIOS (corregida)
CREATE TABLE IF NOT EXISTS Usuarios (
    UsuarioID INT PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    ContrasenaHash VARCHAR(255) NOT NULL,
    Rol ENUM('admin', 'vendedor', 'inventario') NOT NULL DEFAULT 'vendedor',
    Activo BOOLEAN NOT NULL DEFAULT TRUE,
    FechaCreacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UltimoAcceso DATETIME NULL,
    Telefono VARCHAR(20) NULL,
    INDEX idx_usuario_activo (Activo),
    INDEX idx_usuario_rol (Rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA CLIENTES (corregida)
CREATE TABLE IF NOT EXISTS Clientes (
    ClienteID INT PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(100) NOT NULL,
    RUC VARCHAR(20) NULL UNIQUE,
    Direccion TEXT NULL,
    Telefono VARCHAR(20) NULL,
    Email VARCHAR(100) NULL,
    TipoCliente ENUM('normal', 'mayorista', 'corporativo') NOT NULL DEFAULT 'normal',
    Activo BOOLEAN NOT NULL DEFAULT TRUE,
    FechaRegistro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cliente_activo (Activo),
    INDEX idx_cliente_tipo (TipoCliente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA PRODUCTOS (corregida)
CREATE TABLE IF NOT EXISTS Productos (
    ProductoID INT PRIMARY KEY AUTO_INCREMENT,
    Codigo VARCHAR(50) NULL UNIQUE,
    Nombre VARCHAR(100) NOT NULL,
    Descripcion TEXT NULL,
    Cantidad INT NOT NULL DEFAULT 0,
    PrecioVenta DECIMAL(10,2) NOT NULL,
    PrecioCompra DECIMAL(10,2) NOT NULL,
    Tipo ENUM('jeans', 'camisas', 'accesorios', 'otros') NOT NULL DEFAULT 'jeans',
    Proveedor VARCHAR(100) NULL,
    Activo BOOLEAN NOT NULL DEFAULT TRUE,
    FechaCreacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FechaActualizacion DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_cantidad_positiva CHECK (Cantidad >= 0),
    CONSTRAINT chk_precio_positivo CHECK (PrecioVenta > 0),
    INDEX idx_producto_activo (Activo),
    INDEX idx_producto_tipo (Tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA VENTAS (corregida)
CREATE TABLE IF NOT EXISTS Ventas (
    VentaID INT PRIMARY KEY AUTO_INCREMENT,
    ClienteID INT NOT NULL,
    UsuarioID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    Descuento DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    Impuestos DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    Total DECIMAL(12,2) NOT NULL,
    MetodoPago ENUM('efectivo', 'tarjeta', 'transferencia') NOT NULL DEFAULT 'efectivo',
    Estado ENUM('pendiente', 'completada', 'cancelada') NOT NULL DEFAULT 'pendiente',
    Observaciones TEXT NULL,
    FOREIGN KEY (ClienteID) REFERENCES Clientes(ClienteID),
    FOREIGN KEY (UsuarioID) REFERENCES Usuarios(UsuarioID),
    INDEX idx_venta_fecha (Fecha),
    INDEX idx_venta_cliente (ClienteID),
    INDEX idx_venta_estado (Estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Actualizar el campo Total con trigger ya que MySQL tiene limitaciones con generated columns
DELIMITER $$
CREATE TRIGGER calcular_total_venta
BEFORE INSERT ON Ventas
FOR EACH ROW
BEGIN
    SET NEW.Total = NEW.Subtotal + NEW.Impuestos - NEW.Descuento;
END$$
DELIMITER ;

-- TABLA DETALLE_VENTAS (corregida)
CREATE TABLE IF NOT EXISTS DetalleVentas (
    DetalleVentaID INT PRIMARY KEY AUTO_INCREMENT,
    VentaID INT NOT NULL,
    ProductoID INT NOT NULL,
    Cantidad INT NOT NULL,
    PrecioUnitario DECIMAL(10,2) NOT NULL,
    Descuento DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID) ON DELETE CASCADE,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID),
    INDEX idx_detventa_venta (VentaID),
    INDEX idx_detventa_producto (ProductoID),
    CONSTRAINT chk_cantidad_positiva_detalle CHECK (Cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trigger para calcular subtotal en DetalleVentas
DELIMITER $$
CREATE TRIGGER calcular_subtotal_detalle
BEFORE INSERT ON DetalleVentas
FOR EACH ROW
BEGIN
    SET NEW.Subtotal = NEW.Cantidad * (NEW.PrecioUnitario - NEW.Descuento);
END$$
DELIMITER ;

-- TABLA FACTURAS (corregida)
CREATE TABLE IF NOT EXISTS Facturas (
    FacturaID INT PRIMARY KEY AUTO_INCREMENT,
    VentaID INT NOT NULL,
    NumeroFactura VARCHAR(20) NOT NULL UNIQUE,
    FechaEmision DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Subtotal DECIMAL(12,2) NOT NULL,
    Impuestos DECIMAL(12,2) NOT NULL,
    Total DECIMAL(12,2) NOT NULL,
    Estado ENUM('pendiente', 'completada', 'cancelada', 'enviado') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID),
    INDEX idx_factura_numero (NumeroFactura),
    INDEX idx_factura_fecha (FechaEmision)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA ALERTAS (corregida)
CREATE TABLE IF NOT EXISTS Alertas (
    AlertaID INT PRIMARY KEY AUTO_INCREMENT,
    ProductoID INT NOT NULL,
    Tipo ENUM('stock_bajo', 'stock_agotado', 'reabastecimiento') NOT NULL,
    NivelActual INT NOT NULL,
    NivelUmbral INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Leida BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE,
    INDEX idx_alerta_tipo (Tipo),
    INDEX idx_alerta_leida (Leida)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA PEDIDOS (corregida)
CREATE TABLE IF NOT EXISTS Pedidos (
    PedidoID INT PRIMARY KEY AUTO_INCREMENT,
    ClienteID INT NOT NULL,
    UsuarioID INT NOT NULL,
    Fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FechaEntrega DATETIME NULL,
    Estado ENUM('pendiente', 'procesando', 'completado', 'cancelado') NOT NULL DEFAULT 'pendiente',
    Subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    Descuento DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    Total DECIMAL(12,2) NOT NULL,
    Observaciones TEXT NULL,
    FOREIGN KEY (ClienteID) REFERENCES Clientes(ClienteID),
    FOREIGN KEY (UsuarioID) REFERENCES Usuarios(UsuarioID),
    INDEX idx_pedido_estado (Estado),
    INDEX idx_pedido_fecha (Fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trigger para calcular total en Pedidos
DELIMITER $$
CREATE TRIGGER calcular_total_pedido
BEFORE INSERT ON Pedidos
FOR EACH ROW
BEGIN
    SET NEW.Total = NEW.Subtotal - NEW.Descuento;
END$$
DELIMITER ;

-- TABLA DETALLE_PEDIDOS (corregida)
CREATE TABLE IF NOT EXISTS DetallePedidos (
    DetallePedidoID INT PRIMARY KEY AUTO_INCREMENT,
    PedidoID INT NOT NULL,
    ProductoID INT NOT NULL,
    Cantidad INT NOT NULL,
    PrecioUnitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID) ON DELETE CASCADE,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID),
    INDEX idx_detpedido_pedido (PedidoID),
    CONSTRAINT chk_cantidad_positiva_pedido CHECK (Cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLA HISTORICO_PRECIOS (corregida)
CREATE TABLE IF NOT EXISTS HistoricoPrecios (
    HistoricoID INT PRIMARY KEY AUTO_INCREMENT,
    ProductoID INT NOT NULL,
    PrecioAnterior DECIMAL(10,2) NOT NULL,
    PrecioNuevo DECIMAL(10,2) NOT NULL,
    FechaCambio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UsuarioID INT NULL,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE,
    FOREIGN KEY (UsuarioID) REFERENCES Usuarios(UsuarioID) ON DELETE SET NULL,
    INDEX idx_historico_producto (ProductoID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TRIGGER PARA ALERTA DE STOCK BAJO (corregido)
DELIMITER $$

CREATE TRIGGER AlertaStockBajo
AFTER UPDATE ON Productos
FOR EACH ROW
BEGIN
    -- Alerta cuando el stock está bajo
    IF NEW.Cantidad < 10 AND NEW.Cantidad > 0 THEN
        INSERT INTO Alertas (ProductoID, Tipo, NivelActual, NivelUmbral)
        VALUES (NEW.ProductoID, 'stock_bajo', NEW.Cantidad, 10);
    
    -- Alerta cuando el stock se agota
    ELSEIF NEW.Cantidad = 0 THEN
        INSERT INTO Alertas (ProductoID, Tipo, NivelActual, NivelUmbral)
        VALUES (NEW.ProductoID, 'stock_agotado', NEW.Cantidad, 0);
    
    -- Alerta cuando se reabastece
    ELSEIF NEW.Cantidad > OLD.Cantidad AND OLD.Cantidad < 10 THEN
        INSERT INTO Alertas (ProductoID, Tipo, NivelActual, NivelUmbral)
        VALUES (NEW.ProductoID, 'reabastecimiento', NEW.Cantidad, 10);
    END IF;
END$$

DELIMITER ;

-- TRIGGER PARA REGISTRAR CAMBIOS DE PRECIO (corregido)
DELIMITER $$

CREATE TRIGGER RegistroCambioPrecio
AFTER UPDATE ON Productos
FOR EACH ROW
BEGIN
    IF OLD.PrecioVenta <> NEW.PrecioVenta THEN
        INSERT INTO HistoricoPrecios (ProductoID, PrecioAnterior, PrecioNuevo, UsuarioID)
        VALUES (NEW.ProductoID, OLD.PrecioVenta, NEW.PrecioVenta, NULL);
    END IF;
END$$

DELIMITER ;

-- PROCEDIMIENTO: REGISTRAR VENTA (corregido)
DELIMITER $$

CREATE PROCEDURE RegistrarVenta(
    IN p_ClienteID INT,
    IN p_UsuarioID INT,
    IN p_MetodoPago VARCHAR(50),
    IN p_Descuento DECIMAL(10,2),
    IN p_Observaciones TEXT,
    OUT p_VentaID INT
)
BEGIN
    DECLARE v_ClienteActivo BOOLEAN DEFAULT FALSE;
    
    -- Verificar si el cliente existe y está activo
    SELECT Activo INTO v_ClienteActivo FROM Clientes WHERE ClienteID = p_ClienteID;
    
    IF v_ClienteActivo IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente no encontrado';
    ELSEIF NOT v_ClienteActivo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente inactivo';
    END IF;
    
    -- Verificar usuario
    IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE UsuarioID = p_UsuarioID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Usuario no válido';
    END IF;
    
    -- Insertar venta con valores por defecto
    INSERT INTO Ventas (
        ClienteID,
        UsuarioID,
        MetodoPago,
        Descuento,
        Observaciones,
        Subtotal,
        Impuestos,
        Total
    ) VALUES (
        p_ClienteID,
        p_UsuarioID,
        p_MetodoPago,
        IFNULL(p_Descuento, 0),
        p_Observaciones,
        0.00, -- Subtotal inicial
        0.00, -- Impuestos inicial
        0.00  -- Total inicial (se actualizará con triggers)
    );
    
    SET p_VentaID = LAST_INSERT_ID();
END$$

DELIMITER ;

-- PROCEDIMIENTO: AGREGAR DETALLE VENTA (corregido)
DELIMITER $$

CREATE PROCEDURE AgregarDetalleVenta(
    IN p_VentaID INT,
    IN p_ProductoID INT,
    IN p_Cantidad INT,
    IN p_DescuentoUnitario DECIMAL(10,2)
)
BEGIN
    DECLARE v_Precio DECIMAL(10,2) DEFAULT 0;
    DECLARE v_Stock INT DEFAULT 0;
    DECLARE v_ProductoActivo BOOLEAN DEFAULT FALSE;
    
    -- Obtener información del producto
    SELECT PrecioVenta, Cantidad, Activo 
    INTO v_Precio, v_Stock, v_ProductoActivo
    FROM Productos 
    WHERE ProductoID = p_ProductoID;
    
    -- Validaciones
    IF v_Precio IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Producto no encontrado';
    ELSEIF NOT v_ProductoActivo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Producto inactivo';
    ELSEIF v_Stock < p_Cantidad THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente';
    END IF;
    
    -- Insertar detalle
    INSERT INTO DetalleVentas (
        VentaID,
        ProductoID,
        Cantidad,
        PrecioUnitario,
        Descuento,
        Subtotal
    ) VALUES (
        p_VentaID,
        p_ProductoID,
        p_Cantidad,
        v_Precio,
        IFNULL(p_DescuentoUnitario, 0),
        p_Cantidad * (v_Precio - IFNULL(p_DescuentoUnitario, 0))
    );
    
    -- Actualizar stock
    UPDATE Productos 
    SET Cantidad = Cantidad - p_Cantidad
    WHERE ProductoID = p_ProductoID;
    
    -- Actualizar subtotal en venta
    UPDATE Ventas V
    SET Subtotal = (
        SELECT SUM(Subtotal) 
        FROM DetalleVentas 
        WHERE VentaID = p_VentaID
    ),
    Total = (
        SELECT SUM(Subtotal) 
        FROM DetalleVentas 
        WHERE VentaID = p_VentaID
    ) + Impuestos - Descuento
    WHERE VentaID = p_VentaID;
END$$

DELIMITER ;