import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTextEdit, QHBoxLayout
)

from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# ------------------- MODEL -------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price}, quantity={self.quantity})"


# ------------------- VALIDATION -------------------
def validate_product(name, price, quantity):
    if not name or name.strip() == "":
        raise ValueError("❌ Name cannot be empty")

    if price < 0:
        raise ValueError("❌ Price must be >= 0")

    if quantity < 0:
        raise ValueError("❌ Quantity must be >= 0")


# ------------------- DATABASE FUNCTIONS -------------------
def test_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print(" Connection successful!")
    except SQLAlchemyError as error:
        print(f"❌ Connection error: {error}")


def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print(" Tables created successfully!")
    except SQLAlchemyError as error:
        print(f"❌ Error creating tables: {error}")


def create_product(name, price, quantity):
    validate_product(name, price, quantity)

    session = SessionLocal()
    try:
        product = Product(name=name, price=price, quantity=quantity)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    except SQLAlchemyError as error:
        session.rollback()
        raise Exception(f"Database error: {error}")

    finally:
        session.close()


def get_product(product_id):
    session = SessionLocal()
    try:
        return session.query(Product).filter(Product.id == product_id).first()

    except SQLAlchemyError as error:
        raise Exception(f"Database error: {error}")

    finally:
        session.close()


def get_all_products():
    session = SessionLocal()
    try:
        return session.query(Product).all()

    except SQLAlchemyError as error:
        raise Exception(f"Database error: {error}")

    finally:
        session.close()


def update_product(product_id, name, price, quantity):
    validate_product(name, price, quantity)

    session = SessionLocal()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()

        if not product:
            return None

        product.name = name
        product.price = price
        product.quantity = quantity

        session.commit()
        session.refresh(product)
        return product

    except SQLAlchemyError as error:
        session.rollback()
        raise Exception(f"Database error: {error}")

    finally:
        session.close()


def delete_product(product_id):
    session = SessionLocal()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()

        if not product:
            return False

        session.delete(product)
        session.commit()
        return True

    except SQLAlchemyError as error:
        session.rollback()
        raise Exception(f"Database error: {error}")

    finally:
        session.close()


class ProductGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Monolithic Product Manager (PyQt5 + PostgreSQL)")
        self.setGeometry(200, 200, 600, 500)

        layout = QVBoxLayout()

        # Inputs
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Product ID (for update/delete/search)")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price (>=0)")

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity (>=0)")

        layout.addWidget(QLabel("Product ID:"))
        layout.addWidget(self.id_input)

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Price:"))
        layout.addWidget(self.price_input)

        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(self.quantity_input)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton(" Add")
        self.btn_add.clicked.connect(self.add_product)

        self.btn_update = QPushButton(" Update")
        self.btn_update.clicked.connect(self.update_product)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_product)

        self.btn_search = QPushButton(" Search")
        self.btn_search.clicked.connect(self.search_product)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_search)

        layout.addLayout(btn_layout)

        # Show all button
        self.btn_show = QPushButton(" Show All Products")
        self.btn_show.clicked.connect(self.show_products)
        layout.addWidget(self.btn_show)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output)

        self.setLayout(layout)

        # Load all products on start
        self.show_products()

    # ------------------- Helper Methods -------------------
    def clear_inputs(self):
        self.id_input.clear()
        self.name_input.clear()
        self.price_input.clear()
        self.quantity_input.clear()

    def get_inputs_for_create_update(self):
        name = self.name_input.text()
        price = float(self.price_input.text())
        quantity = int(self.quantity_input.text())
        return name, price, quantity

    # ------------------- Button Actions -------------------
    def add_product(self):
        try:
            name, price, quantity = self.get_inputs_for_create_update()
            product = create_product(name, price, quantity)

            QMessageBox.information(self, "Success", f" Product added (ID={product.id})")
            self.show_products()
            self.clear_inputs()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_product(self):
        try:
            product_id = int(self.id_input.text())
            name, price, quantity = self.get_inputs_for_create_update()

            updated = update_product(product_id, name, price, quantity)

            if updated:
                QMessageBox.information(self, "Success", f" Product updated (ID={product_id})")
            else:
                QMessageBox.warning(self, "Not Found", " Product not found")

            self.show_products()
            self.clear_inputs()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_product(self):
        try:
            product_id = int(self.id_input.text())
            success = delete_product(product_id)

            if success:
                QMessageBox.information(self, "Success", f" Product deleted (ID={product_id})")
            else:
                QMessageBox.warning(self, "Not Found", " Product not found")

            self.show_products()
            self.clear_inputs()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def search_product(self):
        try:
            product_id = int(self.id_input.text())
            product = get_product(product_id)

            self.output.clear()

            if product:
                self.output.setText(
                    f" Product Found:\n\n"
                    f"ID: {product.id}\n"
                    f"Name: {product.name}\n"
                    f"Price: {product.price}\n"
                    f"Quantity: {product.quantity}\n"
                )
            else:
                self.output.setText(" Product not found")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def show_products(self):
        try:
            products = get_all_products()
            self.output.clear()

            if not products:
                self.output.setText(" No products found.")
                return

            text_result = " Product List:\n\n"
            for p in products:
                text_result += f"ID={p.id} | Name={p.name} | Price={p.price} | Qty={p.quantity}\n"

            self.output.setText(text_result)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ------------------- MAIN -------------------
if __name__ == "__main__":
    test_connection()
    create_tables()

    app = QApplication(sys.argv)
    window = ProductGUI()
    window.show()
    sys.exit(app.exec_())
