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

    def _get_account_move_line_cos(self, period, account,
                                   debit, credit):
        pool = Pool()
        AccountMoveLine = pool.get('account.move.line')

        move_line = AccountMoveLine(
            period=period,
            account=account,
            debit=debit,
            credit=credit
            )
        return move_line

    def _get_account_move_lines_cos(self, period):
        def get_amount(account, qty, cost):
            if cost == 0:
                return cost
            exp = Decimal(str(10.0 ** -account.currency_digits))
            result = Decimal(qty) * cost
            return result.quantize(exp)

        acc_lines = []
        for line in self.lines:
            if line.product.type != 'goods':
                continue

            diff = line.expected_quantity - line.quantity

            if diff == 0:
                continue

            amount_1 = Decimal('0.0')
            amount_2 = Decimal('0.0')

            if diff > 0:
                amount_1 = line.product.cost_price
            else:
                amount_2 = line.product.cost_price
            diff = abs(diff)

            line_debit = self._get_account_move_line_cos(
                period,
                line.product.account_cost_of_sale_used,
                get_amount(
                    line.product.account_cost_of_sale_used,
                    diff, amount_1),
                get_amount(
                    line.product.account_cost_of_sale_used,
                    diff, amount_2),
                )
            line_credit = self._get_account_move_line_cos(
                period,
                line.product.account_expense_used,
                get_amount(
                    line.product.account_expense_used,
                    diff, amount_2),
                get_amount(
                    line.product.account_expense_used,
                    diff, amount_1),
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
            inventory.account_move = acc_move
            invs.append(inventory)

        AccountMove.save(acc_moves)
        cls.save(invs)
