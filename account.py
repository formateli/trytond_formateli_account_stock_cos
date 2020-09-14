# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelSQL, ValueMixin, fields


class Configuration(metaclass=PoolMeta):
    __name__ = 'account.configuration'
    stock_journal = fields.MultiValue(fields.Many2One(
        'account.journal', "Stock Journal", required=True))

    @classmethod
    def default_stock_journal(cls, **pattern):
        return cls.multivalue_model('stock_journal').default_stock_journal()


class ConfigurationStockJournal(ModelSQL, ValueMixin):
    "Account Configuration Stock Journal"
    __name__ = 'account.configuration.stock_journal'
    stock_journal = fields.MultiValue(fields.Many2One(
        'account.journal', "Stock Journal", required=True))

    @classmethod
    def default_stock_journal(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('account', 'journal_stock')
        except KeyError:
            return None


class AccountMove(metaclass=PoolMeta):
    __name__ = 'account.move'

    @classmethod
    def _get_origin(cls):
        return super(AccountMove, cls)._get_origin() + ['stock.inventory']