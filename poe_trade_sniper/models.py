
class POEItem:
    def __init__(self, id, name, price, price_units, price_in_chaos, league, stash_name, owner_name, alerted):
        from poe_trade_sniper.currency import convert_currency_to_chaos
        self.id = id
        self.name = name
        self.price = price
        self.price_units = price_units
        self.league = league
        self.stash_name = stash_name
        self.owner_name = owner_name
        self.alerted = alerted
        self.average_price = None
        self.price_in_chaos = price_in_chaos
        #self.price_in_chaos = convert_currency_to_chaos(self.price_units, self.price)

