#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import pdb
import logging
import datetime
import argparse
import traceback
import importlib

import datetime as dt

from billy.core import settings, base_arg_parser
from billy.scrape import ScrapeError

from billy.bin.update import _get_configured_scraper, _clear_scraped_data


def _run_expenditure_scraper(scraper_type, options):
    scraper = _get_configured_scraper(scraper_type, options, metadata=None)
    if not scraper:
        return [{
            "type": scraper_type,
            "start_time": dt.datetime.utcnow(),
            "noscraper": True,
            "end_time": dt.datetime.utcnow()
        }]

    runs = []

    scrape = {"type": scraper_type}
    scrape['start_time'] = dt.datetime.utcnow()

    # run scraper against year/session/term
    for fiscal_year in options.fiscal_years:
        scraper.scrape(fiscal_year)

        if not scraper.object_count:
            raise ScrapeError("%s scraper didn't save any objects" %
                              scraper_type)

    scrape['end_time'] = dt.datetime.utcnow()
    runs.append(scrape)

    return runs


def main():
    try:
        parser = argparse.ArgumentParser(
            description='update expenditure data',
            parents=[base_arg_parser],
        )

        what = parser.add_argument_group(
            'what to scrape', 'flags that help select what data to scrape')
        scrape = parser.add_argument_group('scraper config',
                                           'settings for the scraper')

        parser.add_argument('module', type=str, help='scraper module (eg. nc)')
        what.add_argument('-y', '--year', action='append', dest='fiscal_years',
                          help='fiscal year(s) to scrape', default=[])

        for arg in ('aggregated', 'transactional'):
            what.add_argument('--' + arg, action='append_const', dest='types',
                              const=arg)
        for arg in ('scrape', 'import', 'report'):
            parser.add_argument('--' + arg, dest='actions',
                                action="append_const", const=arg,
                                help='only run %s step' % arg)

        # special modes for debugging
        scrape.add_argument('--nonstrict', action='store_false', dest='strict',
                            default=True, help="don't fail immediately when"
                            " encountering validation warning")
        scrape.add_argument('--fastmode', help="scrape in fast mode",
                            action="store_true", default=False)
        parser.add_argument('--pdb', action='store_true', default=False,
                            help='invoke PDB when exception is raised')
        parser.add_argument('--ipdb', action='store_true', default=False,
                            help='invoke iPDB when exception is raised')
        parser.add_argument('--pudb', action='store_true', default=False,
                            help='invoke PuDB when exception is raised')

        # scrapelib overrides
        scrape.add_argument('-r', '--rpm', action='store', type=int,
                            dest='SCRAPELIB_RPM')
        scrape.add_argument('--timeout', action='store', type=int,
                            dest='SCRAPELIB_TIMEOUT')
        scrape.add_argument('--retries', type=int,
                            dest='SCRAPELIB_RETRY_ATTEMPTS')
        scrape.add_argument('--retry_wait', type=int,
                            dest='SCRAPELIB_RETRY_WAIT_SECONDS')

        args = parser.parse_args()

        if args.pdb or args.pudb or args.ipdb:
            _debugger = pdb
            if args.pudb:
                try:
                    import pudb
                    _debugger = pudb
                except ImportError:
                    pass
            if args.ipdb:
                try:
                    import ipdb
                    _debugger = ipdb
                except ImportError:
                    pass

            # turn on PDB-on-error mode
            # stolen from http://stackoverflow.com/questions/1237379/
            # if this causes problems in interactive mode check that page
            def _tb_info(type, value, tb):
                traceback.print_exception(type, value, tb)
                _debugger.pm()
            sys.excepthook = _tb_info

        # inject scraper paths so scraper module can be found
        for newpath in settings.SCRAPER_PATHS:
            sys.path.insert(0, newpath)

        # get metadata
        module = importlib.import_module(args.module)
        metadata = module.metadata
        module_settings = getattr(module, 'settings', {})
        abbrev = metadata['abbreviation']

        # load module settings, then command line settings
        settings.update(module_settings)
        settings.update(args)

        # make output dir
        args.output_dir = os.path.join(settings.BILLY_DATA_DIR, abbrev)

        if not args.actions:
            args.actions = ['scrape', 'import', 'report']
        if not args.types:
            args.types = ['transactional', 'aggregated']
        # default to last year for FY
        if not args.fiscal_years:
            args.fiscal_years = [str(datetime.datetime.now().year)]

        plan = "billy-expenditures abbr=%s actions=%s types=%s years=%s" % (
            args.module, ','.join(args.actions), ','.join(args.types), 
            ','.join(args.fiscal_years))
        logging.getLogger('billy').info(plan)

        if 'scrape' in args.actions:
            _clear_scraped_data(args.output_dir, 'expenditures')
            for stype in args.types:
                _run_expenditure_scraper(stype + '_expenditures', args)

        #if 'import' in args.actions:
        #    _do_imports(abbrev, args)

        #if 'report' in args.actions:
        #    _do_reports(abbrev, args)

    except ScrapeError as e:
        logging.getLogger('billy').critical('Error: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
