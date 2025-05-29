from flask import Blueprint, render_template, request, redirect
from db_config import get_db_connection as get_connection
from flask import jsonify  # Asegúrate de importar esto


api_pedidos = Blueprint('api_pedidos', __name__)

@api_pedidos.route('/pedidos', methods=['GET', 'POST'])
def pedidos():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cliente = request.form['cliente_id']
        fecha_entrega = request.form['fecha_entrega']
        estado = request.form['estado']
        subtotal = request.form['subtotal']
        descuento = request.form['descuento']
        total = float(subtotal) - float(descuento)
        observaciones = request.form['observaciones']
        productos = request.form.getlist('productos[]')

        usuario = 1
        cursor.execute("""
            INSERT INTO Pedidos (ClienteID, UsuarioID, FechaEntrega, Estado, Subtotal, Descuento, Total, Observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cliente, usuario, fecha_entrega, estado, subtotal, descuento, total, observaciones))
        pedido_id = cursor.lastrowid

        for prod_id in productos:
            cursor.execute("INSERT INTO detallePedidos (PedidoID, ProductoID) VALUES (%s, %s)", (pedido_id, prod_id))

        conn.commit()

    # IMPORTANTE: crea nuevo cursor para la consulta SELECT
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.PedidoID, 
            c.Nombre, 
            p.UsuarioID, 
            p.Fecha, 
             
            p.Estado, 
            p.Subtotal, 
            p.Descuento, 
            p.Total, 
            p.Observaciones,
            GROUP_CONCAT(pr.Nombre SEPARATOR ', ') AS productos
        FROM Pedidos p
        JOIN Clientes c ON p.ClienteID = c.ClienteID
        LEFT JOIN detallePedidos dp ON dp.PedidoID = p.PedidoID
        LEFT JOIN Productos pr ON pr.ProductoID = dp.ProductoID
        GROUP BY p.PedidoID
        ORDER BY p.Fecha DESC
    """)
    pedidos = cursor.fetchall()
    conn.close()
    

    return render_template('pedidos.html', pedidos=pedidos)



@api_pedidos.route('/api/clientes')
def api_clientes():
    filtro = request.args.get('filtro', '')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ClienteID, Nombre FROM Clientes WHERE Nombre LIKE %s", ('%' + filtro + '%',))
    clientes = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(clientes)  # <--- SOLUCIÓN AQUÍ

@api_pedidos.route('/api/productos')
def api_productos():
    from flask import jsonify  # Asegúrate de importar esto al inicio
    filtro = request.args.get('filtro', '')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ProductoID, Nombre FROM Productos WHERE Nombre LIKE %s", ('%' + filtro + '%',))
    productos = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(productos)  # ← IMPORTANTE: debe ser jsonify()



@api_pedidos.route('/editar_pedido/<int:pedido_id>', methods=['GET', 'POST'])
def editar_pedido(pedido_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        fecha_entrega = request.form['fecha_entrega']
        estado = request.form['estado']
        subtotal = request.form['subtotal']
        descuento = request.form['descuento']
        total = float(subtotal) - float(descuento)
        observaciones = request.form['observaciones']
        productos = request.form.getlist('productos[]')

        # Actualizar pedido
        cursor.execute("""
            UPDATE Pedidos
            SET ClienteID=%s, FechaEntrega=%s, Estado=%s, Subtotal=%s, Descuento=%s, Total=%s, Observaciones=%s
            WHERE PedidoID=%s
        """, (cliente_id, fecha_entrega, estado, subtotal, descuento, total, observaciones, pedido_id))

        # Borrar productos anteriores y agregar nuevos
        cursor.execute("DELETE FROM detallePedidos WHERE PedidoID=%s", (pedido_id,))
        for prod_id in productos:
            if prod_id:
                cursor.execute("INSERT INTO detallePedidos (PedidoID, ProductoID) VALUES (%s, %s)", (pedido_id, prod_id))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/pedidos')

    # Para GET: obtener pedido con detalles
    cursor.execute("""
        SELECT
          p.PedidoID,
          p.ClienteID,
          c.Nombre AS ClienteNombre,
          p.UsuarioID,
          p.Fecha,
          p.FechaEntrega,
          p.Estado,
          p.Subtotal,
          p.Descuento,
          p.Total,
          p.Observaciones,
          GROUP_CONCAT(dp.ProductoID) AS ProductoIDs,
          GROUP_CONCAT(pr.Nombre) AS ProductoNombres
        FROM Pedidos p
        JOIN Clientes c ON p.ClienteID = c.ClienteID
        LEFT JOIN detallePedidos dp ON dp.PedidoID = p.PedidoID
        LEFT JOIN Productos pr ON pr.ProductoID = dp.ProductoID
        WHERE p.PedidoID = %s
        GROUP BY p.PedidoID
    """, (pedido_id,))
    pedido = cursor.fetchone()

    # Obtener lista completa de clientes para el select
    cursor.execute("SELECT ClienteID, Nombre FROM Clientes")
    clientes = cursor.fetchall()

    # Obtener lista completa de productos para el select dinámico
    cursor.execute("SELECT ProductoID, Nombre FROM Productos")
    productos = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('editar_pedido.html', pedido=pedido, clientes=clientes, productos=productos)





@api_pedidos.route('/cancelar_pedido/<int:pedido_id>', methods=['POST'])
def cancelar_pedido(pedido_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Pedidos SET Estado='cancelado', Total=0, Subtotal=0, Descuento=0
        WHERE PedidoID=%s
    """, (pedido_id,))
    conn.commit()
    conn.close()
    return redirect('/pedidos')


@api_pedidos.route('/eliminar_pedido/<int:pedido_id>', methods=['POST'])
def eliminar_pedido(pedido_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Primero elimina los detalles del pedido (si tienes integridad referencial)
    cursor.execute("DELETE FROM detallePedidos WHERE PedidoID = %s", (pedido_id,))
    
    # Luego elimina el pedido
    cursor.execute("DELETE FROM Pedidos WHERE PedidoID = %s", (pedido_id,))

    conn.commit()
    conn.close()
    return redirect('/pedidos')
