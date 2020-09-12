# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @staticmethod
    def _account_domain(type_):
        if type_ == 'out':
            return ['OR', ('type.revenue', '=', True)]
        elif type_ == 'in':
            return ['OR',
                    ('type.expense', '=', True),
                    ('type.stock', '=', True)
                ]
