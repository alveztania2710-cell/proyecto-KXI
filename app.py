
from flask import Flask, render_template, redirect, url_for, session, request, flash
from datetime import datetime
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("KXI_SECRET_KEY") or secrets.token_hex(32)

PRODUCTS = {
    "air": {
        "name": "KX Air",
        "price": 1499,
        "description": "Audifonos ligeros para todos los dias."
    },
    "bas": {
        "name": "KX Bas",
        "price": 2499,
        "description": "Sonido potente para disfrutar tu musica."
    },
    "pro": {
        "name": "KX Pro",
        "price": 2999,
        "description": "Una experiencia de audio avanzada."
    },
    "max": {
        "name": "KX Max",
        "price": 3499,
        "description": "Comodidad y sonido para largas sesiones."
    }
}


def obtener_carrito():
    carrito = session.get("carrito", {})
    resultado = []
    total = 0

    for product_id, cantidad in carrito.items():
        producto = PRODUCTS.get(product_id)
        if producto and isinstance(cantidad, int) and cantidad > 0:
            subtotal = producto["price"] * cantidad
            resultado.append({
                "id": product_id,
                "name": producto["name"],
                "price": producto["price"],
                "quantity": cantidad,
                "subtotal": subtotal
            })
            total += subtotal

    return resultado, total


@app.route("/")
def inicio():
    destacados = list(PRODUCTS.items())
    return render_template("index.html", destacados=destacados)


@app.route("/catalogo")
def catalogo():
    return render_template("catalogo.html", productos=PRODUCTS)


@app.route("/agregar/<product_id>", methods=["POST"])
def agregar(product_id):
    if product_id not in PRODUCTS:
        flash("No encontramos ese producto.", "error")
        return redirect(url_for("catalogo"))

    carrito = session.get("carrito", {})
    carrito[product_id] = int(carrito.get(product_id, 0)) + 1
    session["carrito"] = carrito
    flash(PRODUCTS[product_id]["name"] + " se agrego al carrito.", "success")
    return redirect(url_for("catalogo"))


@app.route("/carrito")
def carrito():
    items, total = obtener_carrito()
    return render_template("carrito.html", items=items, total=total)


@app.route("/actualizar-carrito", methods=["POST"])
def actualizar_carrito():
    carrito = session.get("carrito", {})

    for product_id in list(carrito.keys()):
        try:
            cantidad = int(request.form.get(product_id, 1))
        except (ValueError, TypeError):
            cantidad = 1

        if cantidad <= 0:
            carrito.pop(product_id, None)
        else:
            carrito[product_id] = min(cantidad, 99)

    session["carrito"] = carrito
    flash("Carrito actualizado.", "success")
    return redirect(url_for("carrito"))


@app.route("/eliminar/<product_id>", methods=["POST"])
def eliminar(product_id):
    carrito = session.get("carrito", {})
    carrito.pop(product_id, None)
    session["carrito"] = carrito
    flash("Producto eliminado del carrito.", "success")
    return redirect(url_for("carrito"))


@app.route("/comprar", methods=["GET", "POST"])
def comprar():
    items, total = obtener_carrito()

    if not items:
        flash("Agrega algun producto antes de comprar.", "error")
        return redirect(url_for("catalogo"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        pago = request.form.get("pago", "")

        if not nombre or not correo or "@" not in correo:
            flash("Escribe tu nombre y un correo valido.", "error")
            return render_template(
                "comprar.html", items=items, total=total
            )

        if pago not in ("credito", "debito"):
            flash("Selecciona un metodo de pago.", "error")
            return render_template(
                "comprar.html", items=items, total=total
            )

        pedidos = session.get("pedidos", [])
        numero = len(pedidos) + 1

        pedido = {
            "numero": numero,
            "nombre": nombre,
            "correo": correo,
            "pago": "Tarjeta de credito" if pago == "credito"
                    else "Tarjeta de debito",
            "items": items,
            "total": total,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "estado": "Pedido de demostracion"
        }

        pedidos.append(pedido)
        session["pedidos"] = pedidos
        session["ultimo_pedido"] = pedido
        session["carrito"] = {}

        return redirect(url_for("pedido"))

    return render_template("comprar.html", items=items, total=total)


@app.route("/pedido")
def pedido():
    pedido_actual = session.get("ultimo_pedido")
    if not pedido_actual:
        return redirect(url_for("inicio"))
    return render_template("pedido.html", pedido=pedido_actual)


@app.route("/ventas")
def ventas():
    pedidos = session.get("pedidos", [])
    ingresos = sum(p["total"] for p in pedidos)
    unidades = sum(
        item["quantity"]
        for pedido in pedidos
        for item in pedido["items"]
    )
    return render_template(
        "ventas.html",
        pedidos=pedidos,
        ingresos=ingresos,
        unidades=unidades
    )


if __name__ == "__main__":
    app.run(debug=True)