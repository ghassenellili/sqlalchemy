from spyne import Application, rpc, ServiceBase, Integer, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from sqlalchemy import create_engine, Column, Integer as SAInteger, String, Float as SAFloat
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


# ------------------- DATABASE CONFIG -------------------
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ------------------- MODEL -------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(SAInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(SAFloat, nullable=False)
    quantity = Column(SAInteger, nullable=False)


Base.metadata.create_all(bind=engine)


# ------------------- VALIDATION -------------------
def validate_product(name, price, quantity):
    if not name or name.strip() == "":
        raise ValueError("Name cannot be empty")
    if price < 0:
        raise ValueError("Price must be >= 0")
    if quantity < 0:
        raise ValueError("Quantity must be >= 0")


def validate_id(pid):
    if pid <= 0:
        raise ValueError("Invalid Product ID (must be > 0)")


# ------------------- SOAP SERVICE -------------------
class ProductService(ServiceBase):

    @rpc(Unicode, Float, Integer, _returns=Unicode)
    def CreateProduct(ctx, name, price, quantity):
        try:
            validate_product(name, price, quantity)

            session = SessionLocal()
            product = Product(name=name, price=price, quantity=quantity)

            session.add(product)
            session.commit()
            session.refresh(product)
            session.close()

            return f"Product created successfully (ID={product.id})"

        except (ValueError, SQLAlchemyError) as e:
            return f"Error: {str(e)}"

    @rpc(Integer, _returns=Unicode)
    def GetProduct(ctx, product_id):
        try:
            validate_id(product_id)

            session = SessionLocal()
            product = session.query(Product).filter(Product.id == product_id).first()
            session.close()

            if not product:
                return "Product not found"

            return f"ID={product.id}, Name={product.name}, Price={product.price}, Quantity={product.quantity}"

        except (ValueError, SQLAlchemyError) as e:
            return f"Error: {str(e)}"

    @rpc(Integer, Unicode, Float, Integer, _returns=Unicode)
    def UpdateProduct(ctx, product_id, name, price, quantity):
        try:
            validate_id(product_id)
            validate_product(name, price, quantity)

            session = SessionLocal()
            product = session.query(Product).filter(Product.id == product_id).first()

            if not product:
                session.close()
                return "Product not found"

            product.name = name
            product.price = price
            product.quantity = quantity

            session.commit()
            session.close()

            return f"Product updated successfully (ID={product_id})"

        except (ValueError, SQLAlchemyError) as e:
            return f"Error: {str(e)}"

    @rpc(Integer, _returns=Unicode)
    def DeleteProduct(ctx, product_id):
        try:
            validate_id(product_id)

            session = SessionLocal()
            product = session.query(Product).filter(Product.id == product_id).first()

            if not product:
                session.close()
                return "Product not found"

            session.delete(product)
            session.commit()
            session.close()

            return f"Product deleted successfully (ID={product_id})"

        except (ValueError, SQLAlchemyError) as e:
            return f"Error: {str(e)}"


# ------------------- SPYNE APPLICATION -------------------
soap_app = Application(
    [ProductService],
    tns="spyne.inventory.soap",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(soap_app)


# ------------------- RUN SERVER -------------------
if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    print("SOAP service running on http://127.0.0.1:8000")
    print("WSDL available at: http://127.0.0.1:8000/?wsdl")

    server = make_server("127.0.0.1", 8000, wsgi_app)
    server.serve_forever()
