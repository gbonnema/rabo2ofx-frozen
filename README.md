* Rabo2ofx *

This program converts the Dutch rabo csv file for non-business
customers to the financial records of OFX which Gnucash
can process. The csv file is available for download for each customer.

I release this software under Copyright and with the user license of GPL version 3 of which the 
text accompanies the software.

** Use **

Open a terminal in the directory where you downloaded the csv file.
Then use the program on that file. It will create an OFX formatted file
in the subdirectory ofx with the same filename and extension of csv replaced by
ofx. Example:

    $ ls -l
    -rw-rw-r--. 1 gbonnema gbonnema 104392 Jan 27 11:05 2017-004-transactions-01-01-to-05-01.csv
	$ ./rabo2ofx 2017-004-transactions-01-01-to-05-01.csv
    TRANSACTIONS: 425
    IN:           2017-004-transactions-01-01-to-05-01.csv
    OUT:          2017-004-transactions-01-01-to-05-01.ofx

The output file is an OFX compliant xml file that Gnucash can process.

** Transfers: accounts in config **

Since version 2.10 the program uses a config file denoting accounts to be downloaded.
An example file is available. Be sure to register your accounts in the config.

The files you download will have transactions for both accounts. Where a transfer
from config.account1 to config.account2 is present, there will be 2 transactions:

	- One from the perspective of config.account1
	- One from the perspective of config.account2

Without measures, these transactions will be registered in your ofx file twice, as different
transactions, causing havoc in your bookkeeping systems.

To prevent double transactions, for all transfers between config.account1 and config.account2,
the program will only translate the transactions from the viewpoint of the first account in
config. This is indepedent of whether they are in the same download or not.

It means that transfers between config.account1 and config.account2 will only show up if and when
config.account1 is downloaded (config.account1 precedes config.account2 in the config file).
In a file with only config.account2, the transfers will be skipped, i.e. not transferred to the
ofx file.

Be sure to create a config file. An example file is present in the distribution.
Remember: order is important.

** Transfers: accounts not in config **

For accounts not in config, **if they are in the same download file**, transfers will only
produce one of two transfer transactions. These unknown accounts will *never* transfer to
a known config account. For multiple unknown accounts, transfers between the unknown acounts
will register only the first account processed.

This is a risk, and thus the program warns if an account is in the download file, that was not
in the config file. Please make sure to always have the accounts you download in the config file.

** Information and warnings **

* The program was developed for a checking account.

* The program can process multiple accounts per file. If processing gets slow, you could
  choose to download only one account per file. It reads the input once per account.
  But beware of transfers.

* The FITID up until 2018 is a construction of transaction data (amount, date etc). From 2018 the 
  Rabobank starts using a serialnumber that is unique per account.

* The file assumes each account is a checking account. This may not be true for all
  your accounts, but the program has no way of knowing this. There is no configuration data.

* The default directory is ofx. If you want to change this, look for default=ofx in the source code.

* Some of the OFX entered data is fake, like signon-data and at the end of each account balance
  amount or balance date. There is no question of any logon session going on, but the OFX file needs
  the info.

** Date semantics: why we use interestdate in stead of date **

The Rabo has decided to present non-business users with an unusual and unnecessary problem. For business users the
field "datum" (date) is filled with "boekdatum" (the bookingdate). This is what one expects. However, for
non-business users the Rabo fills "datum" (date) with "verwerkingsdatum" (the date the Rabo processed the transaction). 
These dates often differ and is not what one expects.

There is no rational explanation for this difference, but there are a consequences. For users with a non-business account. 
The first consequence is that selection is no longer based on the bookingdate, but on the processing date. For end of year payments,
the processingdate is usually in the next year. So choosing payments for a strict period (month, quarter, year), no longer works as 
expected. 

The second consequence is that your bookkeeping will show the wrong date had I used 'datum' instead of 'rentedatum' (interestdate).
Again, think of end of year payments. The bookkeeping program would attribute them to the wrong year.

For that reason I use interestdate in stead of date. It is not what I want and it does not make sense, but the 
Rabo forces this anomaly. I have contacted them through email april 2018. I have saved the email correspondence to date as a pdf file
but have had no further response, neither a correction of the csv-file contents. I don't expect the Rabo bank to change anything
unless more people complain or the problem becomes public.  

** Development **

If anyone has remarks, please create an issue on the github repository gbonnema/rabo2ofx.
If anyone feels like improving the code, please fork the repo and issue a pull request.

Sept 2018, Guus Bonnema.
