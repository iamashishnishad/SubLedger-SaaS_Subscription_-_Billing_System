from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Customer
from app.repositories import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, db: Session, customer_repo: CustomerRepository):
        self.db = db
        self.customer_repo = customer_repo

    def create_customer(self, data: CustomerCreate) -> Customer:
        email = data.email.strip().lower()
        if self.customer_repo.get_by_email(email) is not None:
            raise ConflictError(f"A customer with email {email} already exists")
        customer = self.customer_repo.add(Customer(name=data.name, email=email))
        self.db.commit()
        return customer

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.customer_repo.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def list_customers(self, offset: int = 0, limit: int = 100) -> list[Customer]:
        return self.customer_repo.list(offset=offset, limit=limit)
