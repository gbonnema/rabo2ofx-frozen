#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#        rabo2ofx.py
#
#        Copyright 2015 Guus Bonnema <gbonnema@xs4all.nl>
#
#        Based on source from ing2ofx.py by Arie van Dobben for ING (GPL v 3)
#            Copyright 2013 Arie van Dobben <avandobben@gmail.com>
#
#        This program is free software: you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
The intent of this script is to convert rabo csv files to ofx files. These
csv file you can download when logged in to www.rabo.nl as customer of Rabo.
The intention is to create OFX files for GnuCash (www.gnucash.org).

This script is adapted from ing2ofx.py by Arie van Dobben (Copyright 2013) which
in turn is based on pb2ofx.pl Copyright 2008, 2009, 2010 Peter Vermaas,
originally found @ http://blog.maashoek.nl/2009/07/gnucash-en-internetbankieren/
which is now dead.

Find the ofx specification at http://www.ofx.net/

Conversion of RABO bank download csv file (comma separated).
Started from incomplete and old RABO docs. deducted file structure from live
transactions (web + download).

The RABO csv contains all fields separated by comma's and surrounded by double
quotes. The current (sept 2015) csv file contains the following fields:

    Length    type    offset  description
    18        alfanum    0       Accountnumber from downloaded account (IBAN)
    03        alfanum    1       Currency code    (usually EUR)
    08        date       2       The interest date, format: EEYYMMDD
    01        DC         3       The debit / credit code: 'D' or 'C'
    14        amount     4       Transaction amount, format: 9(11).9(2)
    18        alfanum    5       Counter accountnumber, IBAN format
    24        alfanum    6       The name for the counter account number
    08        date       7       The transaction date, format: EEYYMMDD
    02        alfanum    8       Booking code. Currently values are:
                                ac = acceptgiro,
                                ba = betaalautomaat,
                                bc = betalen contactloos,
                                bg = bankgiro opdracht,
                                cb = crediteuren betaling,
                                ck = chipknip,
                                db = diverse boekingen,
                                eb = bedrijven euro-incasso,
                                ei = euro-incasso,
                                fb = finbox,
                                ga = geldautomaat euro,
                                gb = geldautomaat vv,
                                id = ideal,
                                kh = kashandeling,
                                ma = machtiging,
                                sb = salarisbetaling,
                                tb = eigen rekening,
                                sp = spoedbetaling,
                                CR = tegoed,
                                D  = tekort
    06        alfanum 9           Budgetcode, a free field for budgetting
    32 x 6    alfanum 10 - 15     Description: 6 fields.
                                  For [ba] (betaalautomaat) descr[0] is often
                                  the payee.
    32        alfanum 16          transaction reference
    32        alfanum 17          payee (IncassantID):
                                    often an IBAN number (not necessarily)
    32        alfanum 18          debit authorization code
                                    (Machtigingscode voor incasso)

The last 2 fields are also filled for other than "ma" bookingcode
(for instance for bookingcode "ei").

For bookingcode "db" counter_account_code and counter_account_holder
are not always filled.


"""

import csv
import argparse
import datetime
import os

#
# Version history in a dict to easily present changes
#

MAINTAINERS = {"gbo": "Guus Bonnema"}

HISTORY = {
    "1.0": ("Initial version", "2015-12-30", "gbo"),
    "1.01": ("Correction for description of db: add space between " +
            "name and description.", "2015-12-30", "gbo"),
    "1.02": ("Added sequence to fitid for same amount, same date.",
                "2016-01-02", "gbo")
    }

VERSION = "1.02"
# Needed for version argument
version_string = '%%(prog)s version %s (%s: [%s] %s)' % (VERSION,
            HISTORY[VERSION][2],
            HISTORY[VERSION][1],
            HISTORY[VERSION][0])

""" First parse the command line arguments. """
parser = argparse.ArgumentParser(prog='rabo2ofx',
    description="""
    The intent of this script is to convert rabo csv files to ofx files. These
    csv file you can download when logged in to www.rabo.nl as customer of Rabo.
    The intention is to create OFX files for GnuCash (www.gucash.org).
                                 """)
parser.add_argument('csvfile', help='A csvfile to process')
parser.add_argument('-o, --outfile', dest='outfile',
   help='Output filename', default=None)
parser.add_argument('-d, --directory', dest='dir',
   help='Directory to store output, default is ./ofx', default='ofx')
parser.add_argument('-c, --convert', dest='convert',
   help="Convert decimal separator to dots (.), default is false",
   action='store_true')
parser.add_argument('--version', '-v', action='version',
    version=version_string)
args = parser.parse_args()


class csvfile():
    """ Read the csv file into a list intended for ofx"""

    keyAccount = 'acctNr'
    keyCurrency = 'currency'
    keyInterestDate = 'interestDate'
    keyDebCredCode = 'debCredCode'
    keyAmount = 'amount'
    keyCounterAcctNr = 'counterAcctNr'
    keyCounterAcctName = 'counterAcctName'
    keyTxDate = 'txDate'
    keyBookCode = 'bookCode'
    keyBudgetCode = 'budgetCode'
    keyDescr1 = 'descr1'
    keyDescr2 = 'descr2'
    keyDescr3 = 'descr3'
    keyDescr4 = 'descr4'
    keyDescr5 = 'descr5'
    keyDescr6 = 'descr6'
    keyTxRef = 'txRef'
    keyIncassantID = 'incassantID'
    keyAuthCode = 'authCode'
    ofxTrnType = {'C': 'CREDIT', 'D': 'DEBIT'}

    #Description of book codes for the Rabo
    bookcode = {
          "ac": "acceptgiro",
          "ba": "betaalautomaat",
          "bc": "betalen contactloos",
          "bg": "bankgiro opdracht",
          "cb": "crediteuren betaling",
          "ck": "chipknip",
          "db": "diverse boekingen",
          "eb": "bedrijven euro-incasso",
          "ei": "euro-incasso",
          "fb": "finbox",
          "ga": "geldautomaat euro",
          "gb": "geldautomaat vv",
          "id": "ideal",
          "kh": "kashandeling",
          "ma": "machtiging",
          "sb": "salarisbetaling",
          "tb": "eigen rekening",
          "sp": "spoedbetaling",
          "CR": "tegoed",
          "D": "tekort"
    }

    def __init__(self):
        self.transactions = list()
        #transnr = 0
        self.fitid = {}

        with open(args.csvfile, 'rb') as csvfile:
            fieldnames = (
                        self.keyAccount, self.keyCurrency, self.keyInterestDate,
                        self.keyDebCredCode, self.keyAmount,
                        self.keyCounterAcctNr, self.keyCounterAcctName,
                        self.keyTxDate, self.keyBookCode, self.keyBudgetCode,
                        self.keyDescr1, self.keyDescr2, self.keyDescr3,
                        self.keyDescr4, self.keyDescr5, self.keyDescr6,
                        self.keyTxRef, self.keyIncassantID, self.keyAuthCode
                )
            #Open the csvfile as a Dictreader
            csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"',
            fieldnames=fieldnames)
            linenr = 0
            for row in csvreader:
                linenr = linenr + 1
                if not row:
                    continue
                ofxData = self.create_ofx(linenr, row)
                self.transactions.append(ofxData)

    def map_account(self, row):
        return row[self.keyAccount].replace(" ", "")

    def map_transaction_type(self, row):
        #Map debit credit into ofx TRNTYPE
        if row[self.keyDebCredCode] in self.ofxTrnType:
            trntype = self.ofxTrnType[row[self.keyDebCredCode]]
        else:
            trntype = 'UNKNOWN'
            # TODO message of exception
        return trntype

    def map_date_posted(self, row):
        # The DTPOSTED is in yyyymmdd format, which is compatible
        # with ofx
        return row[self.keyInterestDate]

    def map_amount(self, row):
        amt = row[self.keyAmount]
        if args.convert:
            amt = amt.replace(",", ".")
        # The TRNAMT needs to be converted to negative if applicable
        if row[self.keyDebCredCode] == 'C':
            amt = amt
        else:
            amt = "-" + amt
        return amt

    def map_fitid(self, dcCode, trnamt, dtposted):
        # the FITID is composed of the date and amount
        # plus dcCode
        # for a unique FITID, we add a sequence number per date
        # Warning: don't spread transactions for one date accross import files!
        # Or they will no be processed due to duplicate FITID.
        key = dtposted + trnamt.replace(",", "").replace("-", "") \
                .replace(".", "") + dcCode
        sequence = 0
        if key in self.fitid:
            sequence = self.fitid[key]
            sequence = sequence + 1
        fitid = key + str(sequence)
        self.fitid[key] = sequence
        return fitid

    def map_account_to(self, row):
        return row[self.keyCounterAcctNr]

    def create_ofx(self, linenr, row):
        account = self.map_account(row)
        trntype = self.map_transaction_type(row)
        dtposted = self.map_date_posted(row)
        trnamt = self.map_amount(row)
        fitid = self.map_fitid(row[self.keyDebCredCode], trnamt, dtposted)
        accountto = self.map_account_to(row)
        (name, memo) = self.map_memo_name(row)

        return {'account': account,
                'trntype': trntype, 'dtposted': dtposted,
                'trnamt': trnamt, 'fitid': fitid,
                'name': name, 'accountto': accountto, 'memo': memo}

    def map_memo_name(self, row):
        """Map several description fields to memo and construct name"""
        # Constructing description depends on bookcode

        # in general, we copy counterAcct information
        if row[self.keyCounterAcctNr] and row[self.keyCounterAcctName]:
            glue = " "
        else:
            glue = ""
        name = row[self.keyCounterAcctNr] + glue \
                + row[self.keyCounterAcctName]

        descr = row[self.keyDescr1] + row[self.keyDescr2] \
            + row[self.keyDescr3] + row[self.keyDescr4] \
            + row[self.keyDescr5] + row[self.keyDescr6]
        # For 'db' and 'ba' we create a different description
        if row[self.keyBookCode] == 'ba' and not name:
            name = row[self.keyDescr1]
            descr = row[self.keyDescr2] + row[self.keyDescr3] \
                    + row[self.keyDescr4] \
                    + row[self.keyDescr5] + row[self.keyDescr6]
        elif row[self.keyBookCode] == "db":
            if name:
                glue = " "
            else:
                glue = ""
            name = "[" + row[self.keyBookCode] + "] " \
                    + self.bookcode[row[self.keyBookCode]] + glue \
                    + name

        memo = descr.replace("&", "&amp")
        return (name, memo)


class ofxwriter():
    def __init__(self):
        date = datetime.date.today()
        nowdate = str(date.strftime("%Y%m%d"))

        message_header = """
<OFX>
   <SIGNONMSGSRSV1>
      <SONRS>                            <!-- Begin signon -->
         <STATUS>                        <!-- Begin status aggregate -->
            <CODE>0</CODE>               <!-- OK -->
            <SEVERITY>INFO</SEVERITY>
         </STATUS>
         <DTSERVER>%(nowdate)s</DTSERVER>   <!-- Oct. 29, 1999, 10:10:03 am -->
         <LANGUAGE>ENG</LANGUAGE>        <!-- Language used in response -->
         <DTPROFUP>%(nowdate)s</DTPROFUP>   <!-- Last update to profile-->
         <DTACCTUP>%(nowdate)s</DTACCTUP>   <!-- Last account update -->
         <FI>                            <!-- ID of receiving institution -->
            <ORG>NCH</ORG>               <!-- Name of ID owner -->
            <FID>1001</FID>              <!-- Actual ID -->
         </FI>
      </SONRS>                           <!-- End of signon -->
   </SIGNONMSGSRSV1>
   <BANKMSGSRSV1>
      <STMTTRNRS>                        <!-- Begin response -->
         <TRNUID>1001</TRNUID>           <!-- Client ID sent in request -->
         <STATUS>                     <!-- Start status aggregate -->
            <CODE>0</CODE>            <!-- OK -->
            <SEVERITY>INFO</SEVERITY>
         </STATUS>""" % {"nowdate": nowdate}
        #print message_header

        #create path to ofxfile
        if args.outfile:
            filename = args.outfile
        else:
            filename = args.csvfile.lower().replace("csv", "ofx")

        #if directory does not exists, create it.
        if not os.path.exists(os.path.join(os.getcwd(), args.dir)):
            os.makedirs(os.path.join(os.getcwd(), args.dir))

        filepath = os.path.join(os.getcwd(), args.dir, filename)

        #Initiate a csv object with data in list of dictionaries.
        csv = csvfile()

        #Determine unique accounts and start and end dates
        accounts = set()
        mindate = 999999999
        maxdate = 0

        #print some statistics:
        print "TRANSACTIONS: " + str(len(csv.transactions))
        print "IN:           " + args.csvfile
        print "OUT:          " + filename

        for trns in csv.transactions:
            accounts.add(trns['account'])
            if int(trns['dtposted']) < mindate:
                mindate = int(trns['dtposted'])
            if int(trns['dtposted']) > maxdate:
                maxdate = int(trns['dtposted'])

        #open ofx file, if file exists, gets overwritten
        with open(filepath, 'w') as ofxfile:
            ofxfile.write(message_header)

            for account in accounts:
                message_begin = """
        <STMTRS>                         <!-- Begin statement response -->
           <CURDEF>EUR</CURDEF>
           <BANKACCTFROM>                <!-- Identify the account -->
              <BANKID>RABONL2U</BANKID> <!-- Routing transit or other FI ID -->
              <ACCTID>%(account)s</ACCTID> <!-- Account number -->
              <ACCTTYPE>CHECKING</ACCTTYPE><!-- Account type -->
           </BANKACCTFROM>               <!-- End of account ID -->
           <BANKTRANLIST>                <!-- Begin list of statement trans. -->
              <DTSTART>%(mindate)s</DTSTART>
              <DTEND>%(maxdate)s</DTEND>""" % {"account": account,
                  "mindate": mindate, "maxdate": maxdate}
                ofxfile.write(message_begin)

                for trns in csv.transactions:
                    if trns['account'] == account:
                        message_transaction = """
                  <STMTTRN>
                     <TRNTYPE>%(trntype)s</TRNTYPE>
                     <DTPOSTED>%(dtposted)s</DTPOSTED>
                     <TRNAMT>%(trnamt)s</TRNAMT>
                     <FITID>%(fitid)s</FITID>
                     <NAME>%(name)s</NAME>
                     <BANKACCTTO>
                        <BANKID></BANKID>
                        <ACCTID>%(accountto)s</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                     </BANKACCTTO>
                     <MEMO>%(memo)s</MEMO>
                  </STMTTRN>""" % trns
                        ofxfile.write(message_transaction)

            message_end = """
              </BANKTRANLIST>                   <!-- End list of statement\
                       trans. -->
              <LEDGERBAL>                       <!-- Ledger balance \
                  aggregate -->
               <BALAMT>0</BALAMT>
               <DTASOF>199910291120</DTASOF><!-- Bal date: 10/29/99, \
                   11:20 am -->
            </LEDGERBAL>                      <!-- End ledger balance -->
         </STMTRS>"""
            ofxfile.write(message_end)

            message_footer = """
      </STMTTRNRS>                        <!-- End of transaction -->
   </BANKMSGSRSV1>
</OFX>
      """
            ofxfile.write(message_footer)

if __name__ == "__main__":
    ofx = ofxwriter()
