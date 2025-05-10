USE jeandeiben2;
-- Insertar datos ficticios de productos tipo jeans
INSERT INTO Productos (Codigo, Nombre, Descripcion, Cantidad, PrecioVenta, PrecioCompra, Tipo, Proveedor, Activo) VALUES
('JN001', 'Jeans Clásico Azul', 'Jeans de corte recto color azul oscuro', 50, 59.99, 35.00, 'jeans', 'DenimCo', TRUE),
('JN002', 'Jeans Skinny Negro', 'Jeans ajustados color negro', 35, 65.99, 38.50, 'jeans', 'DenimPro', TRUE),
('JN003', 'Jeans Boyfriend', 'Jeans holgados estilo boyfriend', 28, 69.99, 42.00, 'jeans', 'DenimWorld', TRUE),
('JN004', 'Jeans Rotos', 'Jeans con roturas naturales', 42, 75.99, 45.00, 'jeans', 'DenimArt', TRUE),
('JN005', 'Jeans Slim Fit', 'Jeans ajustados pero cómodos', 31, 62.99, 37.00, 'jeans', 'DenimCo', TRUE),
('JN006', 'Jeans Vintage', 'Jeans estilo retro lavado', 19, 79.99, 48.00, 'jeans', 'DenimVintage', TRUE),
('JN007', 'Jeans High Waist', 'Jeans de talle alto', 23, 72.99, 43.50, 'jeans', 'DenimPro', TRUE),
('JN008', 'Jeans Flare', 'Jeans con corte flare', 15, 85.99, 52.00, 'jeans', 'DenimWorld', TRUE),
('JN009', 'Jeans Mom Fit', 'Jeans estilo mom con cintura alta', 27, 68.99, 41.00, 'jeans', 'DenimArt', TRUE),
('JN010', 'Jeans Jogger', 'Jeans con estilo deportivo', 38, 55.99, 33.00, 'jeans', 'DenimCo', TRUE),
('JN011', 'Jeans Blanco', 'Jeans color blanco lavado', 22, 64.99, 39.00, 'jeans', 'DenimPro', TRUE),
('JN012', 'Jeans Gris', 'Jeans color gris claro', 17, 59.99, 36.00, 'jeans', 'DenimWorld', TRUE),
('JN013', 'Jeans Stretch', 'Jeans con elastano para mayor comodidad', 45, 74.99, 45.00, 'jeans', 'DenimArt', TRUE),
('JN014', 'Jeans Acampanados', 'Jeans estilo años 70', 12, 89.99, 54.00, 'jeans', 'DenimVintage', TRUE),
('JN015', 'Jeans Cargo', 'Jeans con bolsillos tipo cargo', 29, 78.99, 47.00, 'jeans', 'DenimCo', TRUE),
('JN016', 'Jeans Rectos', 'Jeans corte recto clásico', 33, 59.99, 36.00, 'jeans', 'DenimPro', TRUE),
('JN017', 'Jeans Desgastados', 'Jeans con efecto desgastado', 21, 69.99, 42.00, 'jeans', 'DenimWorld', TRUE),
('JN018', 'Jeans Slim Straight', 'Jeans ajustados en muslo y rectos en pierna', 26, 72.99, 44.00, 'jeans', 'DenimArt', TRUE),
('JN019', 'Jeans Negro Slim', 'Jeans negros ajustados', 37, 65.99, 40.00, 'jeans', 'DenimCo', TRUE),
('JN020', 'Jeans Wide Leg', 'Jeans de pierna ancha', 14, 82.99, 50.00, 'jeans', 'DenimPro', TRUE),
('JN021', 'Jeans Carpenter', 'Jeans estilo carpintero', 18, 79.99, 48.00, 'jeans', 'DenimWorld', TRUE),
('JN022', 'Jeans Cropped', 'Jeans cortados a la altura del tobillo', 24, 67.99, 41.00, 'jeans', 'DenimArt', TRUE),
('JN023', 'Jeans Relaxed Fit', 'Jeans holgados cómodos', 32, 59.99, 36.00, 'jeans', 'DenimCo', TRUE),
('JN024', 'Jeans Destroyed', 'Jeans con roturas extremas', 16, 89.99, 54.00, 'jeans', 'DenimPro', TRUE),
('JN025', 'Jeans Tapered', 'Jeans ajustados en tobillo', 29, 74.99, 45.00, 'jeans', 'DenimWorld', TRUE),
('JN026', 'Jeans High Rise', 'Jeans de talle alto ajustado', 21, 76.99, 46.00, 'jeans', 'DenimArt', TRUE),
('JN027', 'Jeans Low Rise', 'Jeans de talle bajo', 13, 64.99, 39.00, 'jeans', 'DenimCo', TRUE),
('JN028', 'Jeans Bootcut', 'Jeans corte bootcut', 27, 69.99, 42.00, 'jeans', 'DenimPro', TRUE),
('JN029', 'Jeans Raw Hem', 'Jeans con dobladillo sin terminar', 19, 72.99, 44.00, 'jeans', 'DenimWorld', TRUE),
('JN030', 'Jeans Colores Pastel', 'Jeans en tonos pastel', 11, 79.99, 48.00, 'jeans', 'DenimArt', TRUE);

-- Insertar algunos clientes para relacionar con ventas
INSERT INTO Clientes (Nombre, RUC, Telefono, Email, TipoCliente) VALUES
('María González', '20123456789', '987654321', 'maria.g@email.com', 'normal'),
('Carlos López', '20123456780', '987654322', 'carlos.l@email.com', 'mayorista'),
('Tienda Jeans Express', '20123456781', '987654323', 'ventas@jeansexpress.com', 'corporativo');

-- Insertar algunos usuarios
INSERT INTO Usuarios (Nombre, Email, ContrasenaHash, Rol) VALUES
('Ana Vendedora', 'ana@jeandaiben.com', SHA2('password123', 256), 'vendedor'),
('Luis Admin', 'luis@jeandaiben.com', SHA2('admin456', 256), 'admin');

-- Insertar algunas ventas de jeans
INSERT INTO Ventas (ClienteID, UsuarioID, Fecha, Subtotal, Descuento, Impuestos, Total, MetodoPago, Estado) VALUES
(1, 1, NOW(), 0, 0, 0, 0, 'efectivo', 'completada'),
(2, 1, NOW(), 0, 0, 0, 0, 'tarjeta', 'completada'),
(3, 2, NOW(), 0, 0, 0, 0, 'transferencia', 'pendiente');

-- Actualizar los totales de ventas (se haría normalmente con los triggers)
UPDATE Ventas SET 
Subtotal = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 1),
Total = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 1)
WHERE VentaID = 1;

UPDATE Ventas SET 
Subtotal = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 2),
Total = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 2)
WHERE VentaID = 2;

UPDATE Ventas SET 
Subtotal = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 3),
Total = (SELECT SUM(Subtotal) FROM DetalleVentas WHERE VentaID = 3)
WHERE VentaID = 3;

-- Insertar detalles de ventas con productos jeans
INSERT INTO DetalleVentas (VentaID, ProductoID, Cantidad, PrecioUnitario, Descuento, Subtotal) VALUES
(1, 1, 2, 59.99, 0, 119.98),
(1, 3, 1, 69.99, 5.00, 64.99),
(2, 5, 3, 62.99, 0, 188.97),
(2, 7, 2, 72.99, 10.00, 135.98),
(3, 10, 5, 55.99, 15.00, 264.95),
(3, 15, 2, 78.99, 0, 157.98);

-- Insertar algunas facturas
INSERT INTO Facturas (VentaID, NumeroFactura, FechaEmision, Subtotal, Impuestos, Total, Estado) VALUES
(1, 'F001-0001', NOW(), 184.97, 33.29, 218.26, 'pagada'),
(2, 'F001-0002', NOW(), 324.95, 58.49, 383.44, 'pagada'),
(3, 'F001-0003', NOW(), 422.93, 76.13, 499.06, 'pendiente');

-- Insertar algunos pedidos de jeans
INSERT INTO Pedidos (ClienteID, UsuarioID, Fecha, Subtotal, Descuento, Total, Estado) VALUES
(2, 1, NOW(), 0, 0, 0, 'pendiente'),
(3, 2, NOW(), 0, 0, 0, 'procesando');

-- Actualizar totales de pedidos
UPDATE Pedidos SET 
Subtotal = (SELECT SUM(Cantidad * PrecioUnitario) FROM DetallePedidos WHERE PedidoID = 1),
Total = (SELECT SUM(Cantidad * PrecioUnitario) FROM DetallePedidos WHERE PedidoID = 1)
WHERE PedidoID = 1;

UPDATE Pedidos SET 
Subtotal = (SELECT SUM(Cantidad * PrecioUnitario) FROM DetallePedidos WHERE PedidoID = 2),
Total = (SELECT SUM(Cantidad * PrecioUnitario) FROM DetallePedidos WHERE PedidoID = 2)
WHERE PedidoID = 2;

-- Insertar detalles de pedidos con productos jeans
INSERT INTO DetallePedidos (PedidoID, ProductoID, Cantidad, PrecioUnitario) VALUES
(1, 2, 4, 65.99),
(1, 6, 2, 79.99),
(2, 13, 10, 74.99),
(2, 20, 5, 82.99);

-- Generar algunas alertas de stock bajo para jeans
INSERT INTO Alertas (ProductoID, Tipo, NivelActual, NivelUmbral, Fecha) VALUES
(6, 'stock_bajo', 19, 20, NOW()),
(14, 'stock_bajo', 12, 15, NOW()),
(27, 'stock_bajo', 13, 15, NOW());


