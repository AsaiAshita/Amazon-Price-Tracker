# Amazon-Price-Tracker
A script-based Amazon price tracker, written in Python, using sqlite3 and equipped with a NodeJS-powered dashboard.

This script was made to automatically manage the process of checking prices for products sold on Amazon. Instead of keeping multiple tabs open just to check whether something you want to buy has hit a lower price, you can simply use this script to locally automate this process.

# Features
This script comes bundled with various features, such as:
- A local database storing many relevant details of each product
- The possibility of providing a file with multiple Amazon links to be inserted in the database, instead of having to execute the script individually for each one of them
- A series of commands to actively manage your local database
- Automatically updates the lowest ever seen price whenever you execute the script, telling you precisely when such value was seen
- A local price chart of every product in the database
- The ability to print such a price chart directly in the terminal...
- ...or of looking at more information using the bundled dashboard! 

# Requirements
Simply install the dependencies contained in `requirements.txt` by using pip: 
```
pip install -r requirements.txt
```
If you also want to use the dashboard, you will also have to install the necessary NodeJS dependencies. To do this, execute the following from the root folder:
```
cd dashboard
npm install
```
# Usage
```
python3 amazon_price_tracker.py [-l | -p[v] | -d[p] | -fi | -web | -plt | <link> | -h] [ <file.txt> | <string>]
```
where:
```
-l = take the links from <file.txt> and executes the script for each one of them
-p = print all the items in the database together with their lowest ever seen price and the date in which this happened
-pv = same as -p, but it omits those items that have a dummy price (=999)
-d = returns all the items that have <string> in their name and gives the user the ability to delete any one of them
-dp = deletes the entire price history stored in the database
-fi = fetches the link to the image showed in the Amazon page associated to each object in the database and saves it (legacy, you should have no reason to use it, apart from possible broken links)
-web = launches the dashboard in your default browser. NOTE: when you are done, remember to click Ctrl + C to shut down the local server
-plt = fetches all items that have <string> in their name and gives the user the ability to select for which to print the price history plot in the terminal
-h = prints how you can use the script
<link> = an Amazon link - the less tracking clutter, the better
<file.txt> = a .txt file containing, for each line, an Amazon link pointing to the item you want the price of
<string> = a string of text
```
If executed with no arguments, the script updates the price of the items stored in the local database

# Deleting the database
If you want to delete the entire database, simply delete the .db file contained in the /data folder (which the script will automatically create whenever it is first launched).

# List of TODO
- At the moment, the script only takes the price Amazon shows on the page, instead of the entire price list. This can lead to situations where no price is found, even though there is a vendor selling the item.
- Following the above, the script makes no difference between used and new prices. This is something that may be worked upon in the future
- Ulterior features may be included, if they are useful to the objectives of this project
