# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart, get_fiscalyear
import datetime
from decimal import Decimal


class AccountStockCosTestCase(ModuleTestCase):
    'Test account_stock_cos module'
    module = 'account_stock_cos'

    @with_transaction()
    def test_account_stock_cos(self):
        pool = Pool()
        Account = pool.get('account.account')
        AccountMoveLine = pool.get('account.move.line')
        Configuration = pool.get('account.configuration')
        Purchase = pool.get('purchase.purchase')
        PurchaseLine = pool.get('purchase.line')
        Invoice = pool.get('account.invoice')
        StockMove =  pool.get('stock.move')

        party = self._create_party('Supplier test')

        company = create_company()
        with set_company(company):
            create_chart(company)
            self._create_fiscalyear(company)

            account_revenue, = Account.search([
                    ('name', '=', 'Main Revenue'),
                    ])
            account_stock, = Account.search([
                    ('name', '=', 'Stock'),
                    ])
            account_stock_cos, = Account.search([
                    ('name', '=', 'Cost of Sale'),
                    ])

            self.assertEqual(account_stock.type.statement, 'balance')
            self.assertEqual(account_stock.type.stock, True)
            self.assertEqual(account_stock_cos.type.expense, True)
            self.assertEqual(account_stock_cos.type.stock, True)

            product, uom = self._create_product(
                        'Stock product',
                        account_revenue,
                        account_stock,
                        account_stock_cos)

            date = datetime.date.today()

            payment_term = self._set_purchase_config(company)
            warehouse = self._get_warehouse()

            # Purchase

            purchase_line = PurchaseLine(
                    product=product,
                    quantity=100.0,
                    unit=uom,
                    unit_price=Decimal('5.0')
                )

            purchase = Purchase(
                purchase_date=date,
                payment_term=payment_term,
                party=party,
                invoice_address=party.addresses[0],
                warehouse=warehouse,
                lines=[purchase_line]
                )
            purchase.save()

            Purchase.quote([purchase])
            Purchase.confirm([purchase])
            Purchase.process([purchase])

            # Invoice

            invoice = Invoice.search([])[0]
            invoice.invoice_date = date
            Invoice.post([invoice])

            # Stock Move

            move = StockMove.search([])[0]
            StockMove.do([move])

            self.assertEqual(product._get_storage_quantity(), 100.0)

            # Inventory

            inventory = self._get_inventory(
                    company, date, warehouse.input_location,
                    product, uom, 100.0)

            self.assertEqual(inventory.lines[0].expected_quantity, 100.0)

            inventory.confirm([inventory])

            # No account move because product were not affected
            # quantity == expected_quantity
            self.assertEqual(inventory.account_move, None)

            # Inventory
            # quantity < expected_quantity

            inventory = self._get_inventory(
                    company, date, warehouse.input_location,
                    product, uom, 75.0)
            inventory.confirm([inventory])

            self.assertEqual(product._get_storage_quantity(), 75.0)
            self.assertTrue(inventory.account_move)

            line_debit = AccountMoveLine.search([
                    ('move', '=', inventory.account_move.id),
                    ('account', '=', account_stock_cos.id),
                ])[0]
            self.assertEqual(line_debit.debit, Decimal('125.0'))

            line_credit = AccountMoveLine.search([
                    ('move', '=', inventory.account_move.id),
                    ('account', '=', account_stock.id),
                ])[0]
            self.assertEqual(line_credit.credit, Decimal('125.0'))

            # Inventory
            # quantity > expected_quantity

            inventory = self._get_inventory(
                    company, date, warehouse.input_location,
                    product, uom, 100.0)
            inventory.confirm([inventory])

            self.assertEqual(product._get_storage_quantity(), 100.0)
            self.assertTrue(inventory.account_move)

            line_debit = AccountMoveLine.search([
                    ('move', '=', inventory.account_move.id),
                    ('account', '=', account_stock.id),
                ])[0]
            self.assertEqual(line_debit.debit, Decimal('125.0'))

            line_credit = AccountMoveLine.search([
                    ('move', '=', inventory.account_move.id),
                    ('account', '=', account_stock_cos.id),
                ])[0]
            self.assertEqual(line_credit.credit, Decimal('125.0'))


    def _get_inventory(self, company, date, location, product, uom, qty):
        pool = Pool()
        Inventory = pool.get('stock.inventory')
        InventoryLine = pool.get('stock.inventory.line')

        line = InventoryLine(
            product=product,
            uom=uom,
            quantity=qty
            )

        inventory = Inventory(
            date=date,
            location=location,
            company=company,
            lines=[line]
            )
        inventory.save()

        return inventory

    def _get_warehouse(self):
        pool = Pool()
        Location = pool.get('stock.location')
        return Location.search([('code', '=', 'WH')])[0]

    def _create_product(self, name, acc_income, acc_expense, account_stock_cos):
        pool = Pool()
        ProductCategory = pool.get('product.category')
        ProductTemplate = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')

        category = ProductCategory(
            name='Category',
            accounting=True,
            account_expense=acc_expense,
            account_revenue=acc_income,
            account_cost_of_sale=account_stock_cos,
            )
        category.save()

        uom = Uom.search([('symbol', '=', 'u')])[0]

        tmpl = ProductTemplate(
            name=name,
            type='goods',
            list_price=0.0,
            cost_price_method='average',
            purchasable=True,
            purchase_uom=uom,
            default_uom=uom,
            account_category=category,
            )
        tmpl.save()
        product = Product(template=tmpl)
        product.save()

        return product, uom

    def _create_party(self, name):
        pool = Pool()
        Party = pool.get('party.party')
        Address = pool.get('party.address')
        addr = Address(
            name=name,
            )
        party = Party(
            name=name,
            addresses=[addr],
            )
        party.save()
        return party

    def _create_fiscalyear(self, company):
        pool = Pool()
        FiscalYear = pool.get('account.fiscalyear')
        InvoiceSequence = pool.get(
            'account.fiscalyear.invoice_sequence')

        invoice_seq = self._create_sequence(
            'Invoice Sequence', 'account.invoice', company.id, True)

        seq = InvoiceSequence()
        seq.company = company
        seq.out_invoice_sequence = invoice_seq
        seq.out_credit_note_sequence = invoice_seq
        seq.in_invoice_sequence = invoice_seq
        seq.in_credit_note_sequence = invoice_seq

        fy = get_fiscalyear(company)
        fy.invoice_sequences = [seq]
        fy.save()
        FiscalYear.create_period([fy])

    def _set_purchase_config(self, company):
        pool = Pool()
        Config = pool.get('purchase.configuration')

        seq = self._create_sequence(
                'Purchase',
                'purchase.purchase',
                company)

        config = Config(1)
        config.purchase_sequence = seq
        config.save()

        return self._get_payment_term()

    def _get_payment_term(self):
        pool = Pool()
        Payment = pool.get('account.invoice.payment_term')
        Line = pool.get('account.invoice.payment_term.line')

        payment = Payment.search([('name', '=', 'NOW')])

        line = Line(
            type='remainder'
            )
        payment = Payment(
            name='NOW',
            lines=[line]
            )
        payment.save()
        return payment

    def _create_sequence(self, name, code, company, is_strict=False):
        pool = Pool()
        if is_strict:
            Sequence = pool.get('ir.sequence.strict')
        else:
            Sequence = pool.get('ir.sequence')
        seq = Sequence(
            name=name,
            code=code,
            company=company,
            type='incremental'
            )
        seq.save()
        return seq


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountStockCosTestCase))
    return suite
