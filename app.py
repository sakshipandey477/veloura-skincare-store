from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "veloura_secret"

def get_db():
    conn = sqlite3.connect("veloura.db")
    conn.row_factory = sqlite3.Row
    return conn

def is_admin():
    return "username" in session and session.get("role") == "admin"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        session["username"] = user["username"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")
        else:
            return redirect("/shop")

    return redirect("/login?error=invalid")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, "user")
        )
        conn.commit()
        conn.close()
        return redirect("/login")

    except:
        conn.close()
        return redirect("/register?error=exists")

@app.route("/admin")
def admin():
    if not is_admin():
        return redirect("/login")

    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    return render_template("dashboard.html", products=products)

@app.route("/add_product", methods=["POST"])
def add_product():
    if not is_admin():
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]
    image = request.form["image"]

    conn = get_db()
    conn.execute(
        "INSERT INTO products (name, price, image) VALUES (?, ?, ?)",
        (name, price, image)
    )
    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/delete_product/<int:id>")
def delete_product(id):
    if not is_admin():
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/edit_product/<int:id>")
def edit_product_page(id):
    if not is_admin():
        return redirect("/login")

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit_product.html", product=product)

@app.route("/update_product/<int:id>", methods=["POST"])
def update_product(id):
    if not is_admin():
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]
    image = request.form["image"]

    conn = get_db()
    conn.execute(
        "UPDATE products SET name=?, price=?, image=? WHERE id=?",
        (name, price, image, id)
    )
    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/shop")
def shop():
    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    cart_count = 0

    if "username" in session:
        result = conn.execute(
            """
            SELECT SUM(quantity)
            FROM cart
            WHERE username=?
            """,
            (session["username"],)
        ).fetchone()

        if result[0]:
            cart_count = result[0]

    conn.close()

    return render_template(
        "shop.html",
        products=products,
        cart_count=cart_count
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    conn = get_db()

    existing_item = conn.execute(
        "SELECT * FROM cart WHERE product_id=? AND username=?",
        (product_id, username)
    ).fetchone()

    if existing_item:
        conn.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE product_id=? AND username=?
            """,
            (product_id, username)
        )
    else:
        conn.execute(
            """
            INSERT INTO cart (product_id, username, quantity)
            VALUES (?, ?, 1)
            """,
            (product_id, username)
        )

    conn.commit()
    conn.close()

    return redirect("/shop?message=added")

@app.route("/cart")
def cart():
    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    conn = get_db()

    cart_items = conn.execute("""
        SELECT
            cart.id AS cart_id,
            cart.quantity,
            products.*
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.username = ?
    """, (username,)).fetchall()

    conn.close()

    return render_template("cart.html", products=cart_items)

@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    if "username" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute(
        "DELETE FROM cart WHERE id=? AND username=?",
        (cart_id, session["username"])
    )
    conn.commit()
    conn.close()

    return redirect("/cart")

@app.route("/increase_quantity/<int:cart_id>")
def increase_quantity(cart_id):
    if "username" not in session:
        return redirect("/login")

    conn = get_db()
    conn.execute(
        "UPDATE cart SET quantity = quantity + 1 WHERE id=? AND username=?",
        (cart_id, session["username"])
    )
    conn.commit()
    conn.close()

    return redirect("/cart")

@app.route("/decrease_quantity/<int:cart_id>")
def decrease_quantity(cart_id):
    if "username" not in session:
        return redirect("/login")

    conn = get_db()

    item = conn.execute(
        "SELECT quantity FROM cart WHERE id=? AND username=?",
        (cart_id, session["username"])
    ).fetchone()

    if item:
        if item["quantity"] > 1:
            conn.execute(
                "UPDATE cart SET quantity = quantity - 1 WHERE id=? AND username=?",
                (cart_id, session["username"])
            )
        else:
            conn.execute(
                "DELETE FROM cart WHERE id=? AND username=?",
                (cart_id, session["username"])
            )

    conn.commit()
    conn.close()

    return redirect("/cart")

if __name__ == "__main__":
    app.run(debug=True)