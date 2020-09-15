# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
try:
    from trytond.modules.account_stock_cos.tests.account_stock_test import suite
except ImportError:
    from .account_stock_test import suite

__all__ = ['suite']
