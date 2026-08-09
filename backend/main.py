from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
import pandas as pd
from sqlalchemy import create_engine


app = FastAPI()

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_engine(
    "mysql+pymysql://root:ubmVuVNFzorFXnnexAwbdWqTdKnuTwcb@sakura.proxy.rlwy.net:29766/railway",
    pool_pre_ping=True
)

templates = Jinja2Templates(directory="templates")

# LOGIN PAGE
@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

# REGISTER PAGE
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
    )

# SAVE USER
@app.post("/register")
def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...)
):

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO users
                (full_name,email,phone,password)
                VALUES
                (:full_name,:email,:phone,:password)
            """),
            {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "password": password
            }
        )

    return RedirectResponse(url="/", status_code=303)

# LOGIN USER
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )
    
@app.post("/login")
def login_user(
    email: str = Form(...),
    password: str = Form(...)
):

    df = pd.read_sql(
        """
        SELECT *
        FROM users
        WHERE email=%s
        AND password=%s
        """,
        engine,
        params=(email, password)
    )

    if df.empty:
        return {"message": "Invalid Email or Password"}

    return RedirectResponse(
        url="/home",
        status_code=303
    )

# ADMIN LOGIN PAGE
@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html"
    )

# ADMIN LOGIN
@app.post("/admin/login")
def admin_login(
    username: str = Form(...),
    password: str = Form(...)
):

    df = pd.read_sql(
        """
        SELECT *
        FROM admins
        WHERE username=%s
        AND password=%s
        """,
        engine,
        params=(username, password)
    )

    if df.empty:
        return {"message": "Invalid Admin Credentials"}

    return RedirectResponse(
        url="/admin/dashboard",
        status_code=303
    )

# ADMIN DASHBOARD
@app.get("/admin/dashboard")
def admin_dashboard(request: Request):

    total_books = pd.read_sql(
        "SELECT COUNT(*) total FROM books",
        engine
    ).iloc[0]["total"]

    total_users = pd.read_sql(
        "SELECT COUNT(*) total FROM users",
        engine
    ).iloc[0]["total"]

    buy_orders = pd.read_sql(
        """
        SELECT COUNT(*) total
        FROM orders
        WHERE order_type='Buy'
        """,
        engine
    ).iloc[0]["total"]

    rent_orders = pd.read_sql(
        """
        SELECT COUNT(*) total
        FROM orders
        WHERE order_type='Rent'
        """,
        engine
    ).iloc[0]["total"]

    pending_rent = pd.read_sql(
        """
        SELECT COUNT(*) total
        FROM orders
        WHERE order_type='Rent'
        AND status='Pending'
        """,
        engine
    ).iloc[0]["total"]

    out_of_stock = pd.read_sql(
        """
        SELECT COUNT(*) total
        FROM books
        WHERE stock=0
        """,
        engine
    ).iloc[0]["total"]

    buy_revenue = pd.read_sql(
        """
        SELECT IFNULL(SUM(amount),0) total
        FROM orders
        WHERE order_type='Buy'
        """
        ,
        engine
    ).iloc[0]["total"]

    rent_revenue = pd.read_sql(
        """
        SELECT IFNULL(SUM(amount),0) total
        FROM orders
        WHERE order_type='Rent'
        """
        ,
        engine
    ).iloc[0]["total"]

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "request": request,
            "total_books": total_books,
            "total_users": total_users,
            "buy_orders": buy_orders,
            "rent_orders": rent_orders,
            "pending_rent": pending_rent,
            "out_of_stock": out_of_stock,
            "buy_revenue": buy_revenue,
            "rent_revenue": rent_revenue
        }
    )

@app.get("/admin/books")
def admin_books(request: Request):

    books = pd.read_sql(
        "SELECT * FROM books ORDER BY title",
        engine
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_book.html",
        context={
            "books": books.to_dict(orient="records")
        }
    )

@app.get("/admin/edit/{isbn}")
def edit_book(request: Request, isbn: str):

    df = pd.read_sql(
        "SELECT * FROM books WHERE isbn=%s",
        engine,
        params=(isbn,)
    )

    if df.empty:
        return {"message": "Book not found"}

    book = df.iloc[0].to_dict()

    return templates.TemplateResponse(
    request=request,
    name="edit_book.html",
    context={
        "book": book
    }
)

@app.post("/admin/update-book")
def update_book(
    isbn: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    rent_price: float = Form(...),
    rent_days: int = Form(...),
    stock: int = Form(...)
):

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE books
                SET
                    title = :title,
                    author = :author,
                    price = :price,
                    rent_price = :rent_price,
                    rent_days = :rent_days,
                    stock = :stock
                WHERE isbn = :isbn
            """),
            {
                "isbn": isbn,
                "title": title,
                "author": author,
                "price": price,
                "rent_price": rent_price,
                "rent_days": rent_days,
                "stock": stock
            }
        )

    return RedirectResponse(
        url="/admin/books",
        status_code=303
    )

@app.get("/admin/delete/{isbn}")
def delete_book(isbn: str):

    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM books
                WHERE isbn = :isbn
            """),
            {
                "isbn": isbn
            }
        )

    return RedirectResponse(
        url="/admin/books",
        status_code=303
    )

# BUY ORDERS
@app.get("/admin/orders")
def admin_orders(request: Request):

    orders = pd.read_sql(
        """
        SELECT *
        FROM orders
        WHERE order_type='Buy'
        ORDER BY order_date DESC
        """,
        engine
    )

    return templates.TemplateResponse(
    request=request,
    name="buy_orders.html",
    context={
        "request": request,
        "orders": orders.to_dict(orient="records")
    }
)

@app.get("/admin/rent-orders")
def rent_orders(request: Request):

    df = pd.read_sql("""
        SELECT *
        FROM orders
        WHERE order_type='Rent'
        ORDER BY id DESC
    """, engine)

    return templates.TemplateResponse(
        request=request,
        name="rent_order.html",
        context={
            "orders": df.to_dict(orient="records")
        }
    )

# HOME PAGE
@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

# 📚 BOOKS API
@app.get("/books")
def get_books():
    df = pd.read_sql("SELECT * FROM books LIMIT 50", engine)
    return df.to_dict(orient="records")

@app.get("/featured")
def featured_books():
    df = pd.read_sql("""
        SELECT * FROM books
        ORDER BY publication_year DESC
        LIMIT 8
    """, engine)

    return df.to_dict(orient="records")

# GET ALL CATEGORIES
@app.get("/categories")
def get_categories():

    df = pd.read_sql("""
        SELECT DISTINCT category
        FROM books
        ORDER BY category
    """, engine)

    return df.to_dict(orient="records")

# CATEGORY PAGE (HTML)
@app.get("/category-page/{category}")
def category_page(request: Request, category: str):

    df = pd.read_sql(
        """
        SELECT *
        FROM books
        WHERE category=%s
        LIMIT 50
        """,
        engine,
        params=(category,)
    )

    return templates.TemplateResponse(
    request=request,
    name="category.html",
    context={
        "request": request,
        "category": category,
        "books": df.to_dict(orient="records")
    }
)

# BOOKS BY CATEGORY API
@app.get("/category/{category}")
def books_by_category(category: str):

    df = pd.read_sql(
        """
        SELECT *
        FROM books
        WHERE category=%s
        LIMIT 50
        """,
        engine,
        params=(category,)
    )

    return df.to_dict(orient="records")

# 📖 BOOK DETAILS API
@app.get("/book/{isbn}")
def book_details(request: Request, isbn: str):

    # Get selected book
    df = pd.read_sql(
        """
        SELECT *
        FROM books
        WHERE isbn=%s
        """,
        engine,
        params=(isbn,)
    )

    if df.empty:
        return {"message": "Book not found"}

    book = df.iloc[0].to_dict()

    # Get more books by same author
    author_books = pd.read_sql(
        """
        SELECT *
        FROM books
        WHERE author=%s
        AND isbn!=%s
        LIMIT 6
        """,
        engine,
        params=(book["author"], isbn)
    )

    return templates.TemplateResponse(
        request=request,
        name="book.html",
        context={
            "request": request,
            "book": book,
            "author_books": author_books.to_dict(orient="records")
        }
    )

@app.get("/buy/{isbn}")
def buy_book(isbn: str):

    return RedirectResponse(
        url=f"/checkout/{isbn}?type=Buy",
        status_code=303
    )

    df = pd.read_sql(
        "SELECT * FROM books WHERE isbn=%s",
        engine,
        params=(isbn,)
    )

    if df.empty:
        return {"message": "Book not found"}

    book = df.iloc[0]

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO orders
                (isbn, title, customer_email, order_type, amount)
                VALUES
                (:isbn, :title, :customer_email, :order_type, :amount)
            """),
            {
                "isbn": book["isbn"],
                "title": book["title"],
                "customer_email": "demo@gmail.com",
                "order_type": "Buy",
                "amount": float(book["price"])
            }
        )

    return RedirectResponse("/success", status_code=303)

@app.get("/rent/{isbn}")
def rent_book(isbn: str):

    return RedirectResponse(
        f"/checkout/{isbn}?type=Rent",
        status_code=303
    )
    df = pd.read_sql(
        "SELECT * FROM books WHERE isbn=%s",
        engine,
        params=(isbn,)
    )

    if df.empty:
        return {"message": "Book not found"}

    book = df.iloc[0]

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO orders
                (isbn, title, customer_email, order_type, amount)
                VALUES
                (:isbn, :title, :customer_email, :order_type, :amount)
            """),
            {
                "isbn": book["isbn"],
                "title": book["title"],
                "customer_email": "demo@gmail.com",
                "order_type": "Rent",
                "amount": float(book["rent_price"])
            }
        )

    return RedirectResponse("/success", status_code=303)

@app.get("/rent-request")
def rent_request(request: Request):
    return templates.TemplateResponse(
        "rent_request.html",
        {
            "request": request
        }
    )

@app.get("/admin/approve/{order_id}")
def approve_order(order_id: int):

    # Get rent_days for this order's book
    df = pd.read_sql(
        """
        SELECT books.rent_days
        FROM orders
        JOIN books
        ON orders.isbn = books.isbn
        WHERE orders.id = %s
        """,
        engine,
        params=(order_id,)
    )

    if df.empty:
        return {"message": "Order not found"}

    rent_days = int(df.iloc[0]["rent_days"])

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE orders
                SET
                    status='Approved',
                    rent_days=:rent_days,
                    return_date=DATE_ADD(CURDATE(), INTERVAL :rent_days DAY)
                WHERE id=:id
            """),
            {
                "id": order_id,
                "rent_days": rent_days
            }
        )

    return RedirectResponse(
        url="/admin/rent-orders",
        status_code=303
    )

@app.get("/success")
def success(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="success.html"
    )

@app.get("/checkout/{isbn}", response_class=HTMLResponse)
def checkout(
    request: Request,
    isbn: str,
    type: str
):

    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={
            "request": request,
            "isbn": isbn,
            "order_type": type
        }
    )

@app.post("/place_order")
def place_order(
    isbn: str = Form(...),
    order_type: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...)
):

    # Get selected book
    df = pd.read_sql(
        "SELECT * FROM books WHERE isbn=%s",
        engine,
        params=(isbn,)
    )

    if df.empty:
        return {"message": "Book not found"}

    book = df.iloc[0]

    # Decide amount based on order type
    if order_type == "Buy":
        amount = float(book["price"])
    else:
        amount = float(book["rent_price"])

    # Save order
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO orders
                (
                    isbn,
                    title,
                    customer_name,
                    customer_email,
                    phone,
                    address,
                    city,
                    pincode,
                    order_type,
                    amount,
                    status
                )
                VALUES
                (
                    :isbn,
                    :title,
                    :customer_name,
                    :customer_email,
                    :phone,
                    :address,
                    :city,
                    :pincode,
                    :order_type,
                    :amount,
                    :status
                )
            """),
            {
                "isbn": book["isbn"],
                "title": book["title"],
                "customer_name": name,
                "customer_email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "pincode": pincode,
                "order_type": order_type,
                "amount": amount,
                "status": "Pending"
            }
        )

                # Reduce stock by 1
        conn.execute(
            text("""
                UPDATE books
                SET stock = stock - 1
                WHERE isbn = :isbn
            """),
            {
                "isbn": isbn
            }
        )

    # Redirect according to order type
    if order_type == "Buy":
        return RedirectResponse(
            url="/success",
            status_code=303
        )
    else:
        return RedirectResponse(
            url="/rent-request",
            status_code=303
        )
    
    

# 🔍 SEARCH API
@app.get("/search")
def search(q: str):
    df = pd.read_sql(
        "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s LIMIT 20",
        engine,
        params=(f"%{q}%", f"%{q}%")
    )
    return df.to_dict(orient="records")

# ❤️ RECOMMENDATION API
@app.get("/recommend/{isbn}")
def recommend(isbn: str):
    try:
        book = pd.read_sql(
            "SELECT * FROM books WHERE isbn=%s",
            engine,
            params=(isbn,)
        )

        if book.empty:
            return {"error": "Book not found"}

        author = book.iloc[0]["author"]

        rec = pd.read_sql(
            "SELECT * FROM books WHERE author=%s LIMIT 10",
            engine,
            params=(author,)
        )

        return rec.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/debug")
def debug():
    df = pd.read_sql("SELECT * FROM books LIMIT 1", engine)
    return df.to_dict(orient="records")

