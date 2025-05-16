from flask import Blueprint, render_template, request, redirect
from db_config import get_db_connection as get_connection


api_pedidos = Blueprint('api_pedidos', __name__)

@api_pedidos.route('/pedidos', methods=['GET', 'POST'])
def pedidos():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cliente = request.form['cliente']
        usuario = request.form['usuario']
        fecha_entrega = request.form['fecha_entrega']
        estado = request.form['estado']
        subtotal = request.form['subtotal']
        descuento = request.form['descuento']
        total = float(subtotal) - float(descuento)
        observaciones = request.form['observaciones']

        cursor.execute("""
            INSERT INTO Pedidos (ClienteID, UsuarioID, FechaEntrega, Estado, Subtotal, Descuento, Total, Observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (cliente, usuario, fecha_entrega, estado, subtotal, descuento, total, observaciones))
        conn.commit()

    cursor.execute("SELECT * FROM Pedidos ORDER BY Fecha DESC")
    pedidos = cursor.fetchall()
    conn.close()

    return render_template('pedidos.html', pedidos=pedidos)

@api_pedidos.route('/editar_pedido/<int:pedido_id>', methods=['GET', 'POST'])
def editar_pedido(pedido_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        estado = request.form['estado']
        subtotal = request.form['subtotal']
        descuento = request.form['descuento']
        total = float(subtotal) - float(descuento)
        observaciones = request.form['observaciones']

        cursor.execute("""
            UPDATE Pedidos 
            SET Estado=%s, Subtotal=%s, Descuento=%s, Total=%s, Observaciones=%s
            WHERE PedidoID=%s
        """, (estado, subtotal, descuento, total, observaciones, pedido_id))
        conn.commit()
        conn.close()
        return redirect('/pedidos')

    cursor.execute("SELECT * FROM Pedidos WHERE PedidoID = %s", (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return render_template('editar_pedido.html', pedido=pedido)


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
