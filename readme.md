* Rabo2ofx *

This program converts the rabo csv file for non-business
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

** Information and warnings **

* The program was developed for a checking account.

* The program can process multiple accounts per file. If processing gets slow, you could
  choose to download only one account per file. It reads the input once per account.

* The FITID up until 2018 is a construction of transaction data (amount, date etc). From 2018 the 
  Rabobank starts using a serialnumber that is unique per account.

* The file assumes each account is a checking account. This may not be true for all
  your accounts, but the program has no way of knowing this. There is no configuration data.

* The default directory is ofx. If you want to change this, look for default=ofx in the source code.

* Some of the OFX entered data is fake, like signon-data and at the end of each account balance
  amount or balance date. There is no question of any logon session going on, but the OFX file needs
  the info.

** Development **

If anyone has remarks, please create an issue on the github repository gbonnema/rabo2ofx.
If anyone feels like improving the code, please fork the repo and issue a pull request.

April 2018, Guus Bonnema.
