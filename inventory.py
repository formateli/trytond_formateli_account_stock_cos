# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import Workflow, ModelView, fields
from trytond.pyson import Eval
from decimal import Decimal


class Inventory(metaclass=PoolMeta):
    __name__ = 'stock.inventory'

    account_move = fields.Many2One('account.move', 'Account Move',
        readonly=True, ondelete='RESTRICT',
        domain=[
            ('company', '=', Eval('company', -1)),
        ],
        depends=['company'])

    def _get_account_move_line_cos(self, period, account, debit, credit):
        pool = Pool()
        AccountMoveLine = pool.get('account.move.line')

        exp = Decimal(str(10.0 ** -account.currency_digits))
        debit = debit.quantize(exp)
        credit =  credit.quantize(exp)

        move_line = AccountMoveLine(
            period=period,
            account=account,
            debit=debit,
            credit=credit
            )
        return move_line

    def _get_account_move_lines_cos(self, period):
        acc_lines = []
        for line in self.lines:
            if line.product.type != 'goods':
                continue
            if line.quantity == line.expected_quantity:
                continue
            line_debit = self._get_account_move_line_cos(
                period,
                line.product.account_cost_of_sale_used,
                line.product.cost_price,
                Decimal('0.0'),
                )
            line_credit = self._get_account_move_line_cos(
                period,
                line.product.account_expense_used,
                Decimal('0.0'),
                line.product.cost_price,
                )
            acc_lines += [line_debit, line_credit]

        return acc_lines

    def _get_acc_move_cos(self):
        pool = Pool()
        AccountMove = pool.get('account.move')
        Period = pool.get('account.period')
        AccountConfiguration = pool.get('account.configuration')

        period_id = Period.find(self.company.id, date=self.date)

        move_lines = self._get_account_move_lines_cos(period_id)
        if not move_lines:
            return

        account_configuration = AccountConfiguration(1)

        move = AccountMove(
            period=period_id,
            journal=account_configuration.stock_journal,
            date=self.date,
            origin=self,
            company=self.company,
            description='Cost of sale by stock inventory', #TODO Translate
            lines=move_lines,
            )

        return move

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def confirm(cls, inventories):
        super(Inventory, cls).confirm(inventories)

        pool = Pool()
        AccountMove = pool.get('account.move')

        acc_moves = []
        invs = []
        for inventory in inventories:
            acc_move = inventory._get_acc_move_cos()
            if acc_move is None:
                continue
            acc_moves.append(acc_move)
            inventory.move = acc_move
            invs.append(inventory)

        AccountMove.save(acc_moves)
        cls.save(invs)
