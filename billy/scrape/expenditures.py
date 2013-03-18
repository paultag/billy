import uuid

from billy.scrape import Scraper, SourcedObject


class TransactionalExpenditureScraper(Scraper):

    scraper_type = 'transactional_expenditures'

    def scrape(self, fiscal_year):
        raise NotImplementedError("TransactionalExpenditureScrapers must "
                                  "define a scrape method")


class AggregatedExpenditureScraper(Scraper):

    scraper_type = 'aggregated_expenditures'

    def scrape(self, fiscal_year):
        raise NotImplementedError("AggregatedExpenditureScrapers must "
                                  "define a scrape method")


class Expenditure(SourcedObject):
    def __init__(self, fiscal_year, spending_type, recipient_name, amount,
                 **kwargs):
        super(Expenditure, self).__init__('expenditure', **kwargs)
        self.uuid = uuid.uuid1()  # consistent uuid across saves

        self['fiscal_year'] = fiscal_year
        self['spending_type'] = spending_type
        self['recipient_name'] = recipient_name
        self['amount'] = amount
        self.update(kwargs)

    def get_filename(self):
        return "%s.json" % str(self.uuid)

    def __unicode__(self):
        return "%s %s %s" % (self['fiscal_year'], self['recipient_name'],
                             self['amount'])


class TransactionalExpenditure(Expenditure):
    def __init__(self, fiscal_year, spending_type, recipient_name, amount,
                 **kwargs):
        super(TransactionalExpenditure, self).__init__(fiscal_year,
                                                       spending_type,
                                                       recipient_name,
                                                       amount, **kwargs)
        self['expenditure_type'] = 'transactional'


class AggregatedExpenditure(Expenditure):
    def __init__(self, fiscal_year, spending_type, recipient_name, amount,
                 **kwargs):
        super(TransactionalExpenditure, self).__init__(fiscal_year,
                                                       spending_type,
                                                       recipient_name,
                                                       amount, **kwargs)
        self['expenditure_type'] = 'aggregated'
