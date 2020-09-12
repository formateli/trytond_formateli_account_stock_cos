# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import fields
from trytond.pyson import Eval, If
from trytond.modules.account_product.product import (
    account_used, template_property)


class Category(metaclass=PoolMeta):
    __name__ = 'product.category'
    account_cost_of_sale = fields.MultiValue(fields.Many2One(
            'account.account', "Account Cost of Sale",
            domain=[
                ('closed', '!=', True),
                ('type.expense', '=', True),
                ('id', 'not in', [
                        Eval('account_expense', -1),
                        Eval('account_revenue', -1)]),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)
                    | Eval('account_cost_of_sale_hide', False))
                },
            depends=['account_parent', 'accounting',
                'account_expense', 'account_revenue',
                'account_cost_of_sale_hide']))
    account_cost_of_sale_hide = fields.Function(
        fields.Boolean('Hide Account Cost of Sale'),
        'on_change_with_account_cost_of_sale_hide')

    @fields.depends('account_expense')
    def on_change_with_account_cost_of_sale_hide(self, name=None):
        if self.account_expense and \
                self.account_expense.type.statement == 'balance':
            return False
        return True

    @classmethod
    def __setup__(cls):
        super(Category, cls).__setup__()

        cls.account_expense.domain[1] = ['OR',
                [
                    ('type.expense', '=', True),
                ],
                [
                    ('type.stock', '=', True),
                    ('type.statement', '=', 'balance'),
                ]
            ]

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'account_cost_of_sale':
            return pool.get('product.category.account')
        return super(Category, cls).multivalue_model(field)

    @property
    @account_used('account_cost_of_sale')
    def account_cost_of_sale_used(self):
        pass


class CategoryAccount(metaclass=PoolMeta):
    __name__ = 'product.category.account'
    account_cost_of_sale = fields.Many2One(
        'account.account', "Account Cost of Sale",
        domain=[
            ('closed', '!=', True),
            ('type.expense', '=', True),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])

    @classmethod
    def __setup__(cls):
        super(CategoryAccount, cls).__setup__()

        cls.account_expense.domain[0] = ['OR',
                [
                    ('type.expense', '=', True),
                ],
                [
                    ('type.stock', '=', True),
                    ('type.statement', '=', 'balance'),
                ]
            ]


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()

        cls.account_category.domain.append(
            If((Eval('type'), '=', 'goods'),
                ('account_expense.type.statement', '=', 'balance'),
                ('account_expense.type.statement', '!=', None)
            )
            )

        cls.account_category.depends += ['type']

    @property
    @account_used('account_cost_of_sale', 'account_category')
    def account_cost_of_sale_used(self):
        pass


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    account_cost_of_sale_used = template_property('account_cost_of_sale_used')
