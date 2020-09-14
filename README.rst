Account Stock Cost of Sale
##########################

Account Stock Cost of Sale for Tryton.

It take care of account moves for products type of 'goods' on Purchases, affecting
cost of sale by Stock Inventories.

When Stock Inventory is made an account move is created, two account move line will be created
for every product affected, one that affect its 'stock' and 'balance statement' account by credit,
and other that affect its 'Cost of Sale' expense account by debit.

- account_expense of product category domain can be type of 'stock' and 'balance statement'.
- If a product is type of 'goods' the account_expense defined in its category
  must be type of 'stock' and 'balance statement', else if product is type of 'service'
  the account_expense must be type of 'expense'.
- Define a new field for product category 'account_cost_of_sale',
  which is the expense cost of sale account. This account is available only if account_expense
  type if 'balance statement'. It is used when Stock Inventory is made.

Installing
----------

Drop 'trytond_formateli_aacount_stock_cos' folder on 'tryrond/modules/' as
'trytond_formateli_aacount_stock_cos' and update Tryton database.

Support
-------

For Tryton framework:

    * https://tryton.org/

For this module

    * https://github.com/formateli/trytond_formateli_aacount_stock_cos

License
-------

See LICENSE

Copyright
---------

See COPYRIGHT


For more information please visit:

    * http://www.tryton.org/
    * https://formateli.com
