# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import product
from . import invoice


def register():
    Pool.register(
        product.Category,
        product.CategoryAccount,
        product.Template,
        product.Product,
        invoice.InvoiceLine,
        module='account_stock_cos', type_='model')
