from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Customer, Flight, Invoice, InvoiceItem, UserProfile
from datetime import datetime

class BaseTestCase(TestCase):
    def setUp(self):
        # Users
        self.admin = User.objects.create_user(username="Admin", password="testpass123")
        UserProfile.objects.create(user=self.admin, role="Admin")

        self.sales = User.objects.create_user(username="sales", password="testpass123")
        UserProfile.objects.create(user=self.sales, role="SalesAgent")

        self.accountant = User.objects.create_user(username="acc", password="testpass123")
        UserProfile.objects.create(user=self.accountant, role="Accountant")

        self.manager = User.objects.create_user(username="mgr", password="testpass123")
        UserProfile.objects.create(user=self.manager, role="Manager")

        # Data
        self.customer = Customer.objects.create(
            name="John Doe",
            email="john@example.com"
        )

        self.flight = Flight.objects.create(
            flight_number="AB123",
            origin="Dublin",
            destination="London",
            departure_time=datetime.now(),
            base_price=100
        )

        self.invoice = Invoice.objects.create(
            customer=self.customer,
            created_by=self.sales,
            status="Pending",
            total=0
        )

        self.client = Client()

# LOGIN TESTS
class LoginTests(BaseTestCase):
    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "username": "sales",
            "password": "testpass123"
        })
        self.assertEqual(response.status_code, 302)

# PERMISSION TESTS
class PermissionTests(BaseTestCase):

    def test_salesagent_can_access_create_invoice(self):
        self.client.login(username="sales", password="testpass123")
        response = self.client.get(reverse("create_invoice"))
        self.assertEqual(response.status_code, 200)

    def test_accountant_cannot_access_create_invoice(self):
        self.client.login(username="acc", password="testpass123")
        response = self.client.get(reverse("create_invoice"))
        self.assertTemplateUsed(response, "no_permission.html")

    def test_manager_cannot_access_add_item(self):
        self.client.login(username="mgr", password="testpass123")
        response = self.client.get(reverse("add_invoice_item", args=[self.invoice.id]))
        self.assertTemplateUsed(response, "no_permission.html")

    def test_accountant_can_update_status(self):
        self.client.login(username="acc", password="testpass123")
        response = self.client.get(reverse("update_invoice_status", args=[self.invoice.id]))
        self.assertEqual(response.status_code, 200)

    def test_salesagent_cannot_update_status(self):
        self.client.login(username="sales", password="testpass123")
        response = self.client.get(reverse("update_invoice_status", args=[self.invoice.id]))
        self.assertTemplateUsed(response, "no_permission.html")

    def test_manager_can_access_report(self):
        self.client.login(username="mgr", password="testpass123")
        response = self.client.get(reverse("customer_report"))
        self.assertEqual(response.status_code, 200)

    def test_salesagent_cannot_access_report(self):
        self.client.login(username="sales", password="testpass123")
        response = self.client.get(reverse("customer_report"))
        self.assertTemplateUsed(response, "no_permission.html")

# INVOICE FUNCTIONALITY TESTS
class InvoiceTests(BaseTestCase):

    def test_salesagent_can_add_invoice_item(self):
        self.client.login(username="sales", password="testpass123")
        response = self.client.post(reverse("add_invoice_item", args=[self.invoice.id]), {
            "flight": self.flight.id,
            "quantity": 2
        })
        self.assertEqual(response.status_code, 302)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total, 200)

    def test_accountant_can_update_status(self):
        self.client.login(username="acc", password="testpass123")
        response = self.client.post(reverse("update_invoice_status", args=[self.invoice.id]), {
            "status": "Approved"
        })
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "Approved")

    def test_admin_can_delete_invoice(self):
        self.client.login(username="Admin", password="testpass123")
        response = self.client.get(reverse("delete_invoice", args=[self.invoice.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Invoice.objects.filter(id=self.invoice.id).exists())

# USE CASE TEST
class UseCaseTests(BaseTestCase):
    def test_sales_agent_full_workflow(self):
        """SalesAgent logs in → creates invoice → adds item → total updates"""
        self.client.login(username="sales", password="testpass123")

        # Create invoice
        response = self.client.post(reverse("create_invoice"), {
            "customer": self.customer.id
        })
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.last()

        # Add item
        response = self.client.post(reverse("add_invoice_item", args=[invoice.id]), {
            "flight": self.flight.id,
            "quantity": 2
        })
        self.assertEqual(response.status_code, 302)

        invoice.refresh_from_db()
        self.assertEqual(invoice.total, 200)

    def test_accountant_updates_invoice_status(self):
        """Accountant logs in → opens invoice → updates status"""
        self.client.login(username="acc", password="testpass123")

        response = self.client.post(reverse("update_invoice_status", args=[self.invoice.id]), {
            "status": "Approved"
        })
        self.assertEqual(response.status_code, 302)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "Approved")

    def test_manager_views_customer_report(self):
        """Manager logs in → opens customer report page"""
        self.client.login(username="mgr", password="testpass123")

        response = self.client.get(reverse("customer_report"))
        self.assertEqual(response.status_code, 200)
