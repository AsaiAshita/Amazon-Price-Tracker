import requests #dependance
from bs4 import BeautifulSoup #dependance
import sys
from termcolor import colored #dependance
import sqlite3 #dependance
import datetime
from simple_term_menu import TerminalMenu #dependance
import webbrowser
import subprocess
import os
import time
import plotext as plt #dependance
from urllib.parse import urlparse
from pathlib import Path
from colorama import just_fix_windows_console
from sys import platform



verbose = False #False for verbose mode disabled, True for active - this mode simply provides more details regarding some operations, but that's all
MAX_TRIES = 15 #maximum amount of times the script tries to inquire Amazon for a particular link - feel free to change this to whatever value you like
PORT = 3000 #port on which to open the dashboard
URL = f"http://localhost:{PORT}" #url to the dashboard
customized_plot = True #if enabled, it allows you to customize the plotting in the terminal with the colours of your choice
#refer to https://github.com/piccolomo/plotext/blob/master/readme/aspect.md#colors for customization
DEFAULT_THEME = "elegant"
ticks_color = "black" 
canvas_color = "orange+"
axis_color = 110 
marker_color = 126

def print_usage():
    print("\nUsage: python3 amazon_price_tracker.py [-l | -p[v] | -d[p] | -fi | -web | -plt | <link> | -h] [ <file.txt> | <string>]\n"
        "ARGUMENTS:\n\n"
        "-l = take the links from <file.txt>\n"
        "-p = print all the items in the database together with their lowest ever seen price and the date in which this happened\n"
        "-pv = same as -p, but it omits those items that have a dummy price (=999)\n"
        "-d = returns all the items that have <string> in their name and gives the user the ability to delete any one of them\n"
        "-dp = deletes the entire price history stored in the database\n"
        "-fi = fetches the link to the image showed in the Amazon page associated to each object in the database and saves it\n"
        "-web = launches the dashboard in your default browser. NOTE: when you are done, remember to click Ctrl + C to shut down the local server\n"
        "-plt = fetches all items that have <string> in their name and gives the user the ability to select for which to print the price history plot in the terminal"
        "-h = prints how you can use the script\n"
        "<link> = an Amazon link - the less tracking clutter, the better\n"
        "<file.txt> = a .txt file containing, for each line, an Amazon link pointing to the item you want the price of\n"
        "<string> = a string of text\n"
        "\n"
        "If executed with no arguments, the script updates the price of the items stored in the local database")
    return

def is_link(s):
    """
    The following function uses urlparse from urllib.parse in order to check whether a provided link is correct or not
    Used to validate the user input before executing a request
    """
    try:
        result = urlparse(s.strip())
        return result.scheme in ("http", "https") and bool(result.netloc)
    except:
        return False

def start_server():
    """
    The following function starts the web server for the dashboard by running the command "node run_db.js" from the script.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(base, "dashboard", "read_db.js")
    return subprocess.Popen(
        ["node", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def query_amazon(clean_url, img_search=False):
    """
    The following function queries the provided clean_url, parses it to get the title of the item displayed and the price displayed on Amazon
    and then returns them. If one of those is not retrieved, the function returns 2 dummy values (999,999) to signal to the scrip that
    it was unable to retrieve the prices and that it should attempt it again.

    NOTE:
    As of now, this function only returns the displayed Amazon price, without checking whether it is used or new, or whether there are better offers
    provided by other vendors. 
    """
    #we query the provided link
    response = requests.get(clean_url, headers={'Accept': 'application/xml; charset=utf-8','User-Agent':'foo'})
    #if the request didn't return an OK status, we exit
    if response.status_code != 200:
        if verbose:
            print(colored("ERROR: the page was not available\n", "red"))
        return 999,999,"None"
    #parse the resulting HTML page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    #price = soup.findAll("span", class_="a-price")
    #we find the title of the item
    title = soup.find("span", id="productTitle")
    #if it is None, we probably got an error page, so we exit
    if title is None:
        if verbose:
            print(colored("ERROR: the returned page does not have the item's name in it - probably got an error during request", "red"))
        return 999,999,"None"
    #we get the real title from the obtained span and print it
    if title:
        title = title.get_text()
    if verbose:
        print(colored({title}, "green", attrs=['bold']))
    price = soup.select_one("span.a-price") #select the full price that is shown in the page - TODO: make it so that we get all the prices
    #price = set(price)
    #if price is None, something went wrong with the request and we probably got served an error page, so we exit
    if price is None:
        if verbose:
            print(colored("ERROR: no price retrieved!", "red"))
        return 999,title, "None"
    #else, if a price was found, we get its content, remove the euro sign and eliminate every empty value the query may have returned
    elif len(price) != 0:
        price = [p.get_text() for p in price]
        price = [p.replace('€', '') for p in price]
        price = [p.replace(',', '.') for p in price]
        price = [float(p) for p in price if p!=' ']
        if not verbose:
            print(colored({title}, "green", attrs=['bold']))
        print(colored("Current price: " + str(price[0]), "light_grey"))
    #else, if anything else happened, we just exit
    else:
        if verbose:
            print(colored("ERROR: no price retrieved!", "red"))
        return 999,title
    #lastly, if we need to, we search for the image link in the returned page using the dedicated function
    if img_search:
        img_link = fetch_image_from_amazon(clean_url, False, response)
    else:
        img_link = "None"
    #finally, we return the so obtained price, title and link image
    return price, title, img_link  

def fetch_image_from_amazon(clean_url, fetch_link=True, response=None):
    """
    The following function queries the provided clean_url, parses it to get the link to the image displayed and returns it to
    the caller. This function is used to fetch images for links that have been inserted into the database without one.
    This will mostly be used only by the -fi option, otherwise this function should be incorporated into the query_amazon function.
    Used to have a link to call to display images in the dashboard.
    """
    if(fetch_link):
        #we query the provided link
        response = requests.get(clean_url, headers={'Accept': 'application/xml; charset=utf-8','User-Agent':'foo'})
        #if the request didn't return an OK status, we exit
        if response.status_code != 200:
            if verbose:
                print(colored("ERROR: the page was not available\n", "red"))
            return "None"
    #parse the resulting HTML page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    img = soup.find("img", id="landingImage")
    if img:
        image_url = img.get("src")
        return image_url
    else:
        return "None"

def main():
    #if OS is windows, we use Colorama to enable termcolor colored prints
    #this makes the script be able to be launched also on Windows systems.
    if platform == "win32":
        just_fix_windows_console()
    #we get the number of arguments given to the script
    n = len(sys.argv)
    #we connect to sqlite, create a database and create a table called products, if it doesn't already exist
    #conn = sqlite3.connect("./data/amazon_price_history.db")  # creates file if it doesn't exist -> wrongly thought it also created the folder: it doesn't...
    BASE_DIR = Path(__file__).resolve().parent
    db_path = BASE_DIR / "data" / "amazon_price_history.db"
    if not os.path.exists(db_path):
        db_path.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            date TEXT,
            link TEXT,
            image_link TEXT                      
    )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    #usage:
    # - python3 amazon_price_tracker.py (n==1) -> update the price of the items contained in the database
    # - python3 amazon_price_tracker.py <link> (n==2) -> get the price for the provided link and store it in the database
    # - python3 amazon_price_tracker.py -l <file.txt> (n==3) -> get the price for the links contained in <file.txt> and store them in the database
    # - python3 amazon_price_tracker -p (n==2) -> print all the items in the database and their lowest price ever seen, together with the date it appeared
    # - python3 amazon_price_tracker -pv (n==2) -> print all the items in the database and their lowest price ever seen, together with the date it happened, omitting those that have a dummy price (=999)
    # - python3 amazon_price_tracker -d <string> (n==3) -> select all the items in the database with the specific title and let the user select which of these it wants to delete from the database
    # - python3 amazon_price_tracker -fi (n==2) -> fetchs the image link displayed on each amazon link stored in the database and stores it into the db
    # - python3 amazon_price_tracker -web (n==2) -> launches a dashboard in the browser that lets you visualize the items you have in your database, the lowest price ever seen and when it was seen
    # - python3 amazon_price_tracker -dp (n==2) -> deletes the entirety of the stored price history
    # - python3 amazon_price_tracker -plt <string> (n==3) -> lets you choose one of the items in the database with <string> in its name and plots its price history in terminal

    if n == 2:
        if(sys.argv[1] == '-h'):
            print_usage()
            return 0
        if(sys.argv[1] == "-web"):
            #start the server
            proc = start_server()
            time.sleep(2)
            #open the browser at the url of index.html
            webbrowser.open(URL)
            #keep the server up until we receive a keyboard interrupt
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                print("STDOUT:")
                print(stdout.decode())
                print("STDERR:")
                print(stderr.decode())
                exit(99)
            try:
                proc.wait()
            except KeyboardInterrupt:
                print("Stopping server...")
                proc.terminate()
                return 0
        elif(sys.argv[1] == "-p" or sys.argv[1] == "-pv"):
            print(colored("Starting print of all elements contained in the database...", "cyan"))
            if "v" in sys.argv[1]:
                print(colored("Printing only valid items...", "cyan"))
                cursor.execute("SELECT * FROM products WHERE NOT price = 999")
            else:
                cursor.execute("SELECT * FROM products")
            results = cursor.fetchall()
            for row in results:
                print(colored({row[1]}, "green", attrs=['bold']))
                print(colored("Lowest price ever seen: " + str(row[2]) + "\nSeen on date: " + str(row[3]), "yellow"))
            print(colored("Operation completed!", "cyan"))
            return 0
        elif(sys.argv[1] == "-dp"):
            print(colored("Are you sure you really want to delete the entire price history stored locally?", "red"))
            terminal_menu = TerminalMenu(["Yes", "No"])
            menu_entry_index = terminal_menu.show()
            if menu_entry_index == 1:
                print(colored("Operation aborted!", "red"))
            else:
                cursor.execute("DELETE FROM history")
                conn.commit()
                print(colored("Price history deleted successfully", "cyan"))
            return 0
        elif(sys.argv[1] == "-fi"):
            #in this case, we want to query every single amazon page we have stored to get the link to the image displayed on it
            #hence, we query the amazon page, get the link and update the database with it
            print(colored("Fetching image links for all elements in the database...", "cyan"))
            if verbose:
                print("Verbose mode active")
            cursor.execute("SELECT * FROM products")
            results = cursor.fetchall()
            for row in results:
                link = row[4]
                img = "None"
                tries = 0
                while img == "None" and tries < MAX_TRIES:
                    img = fetch_image_from_amazon(link)
                if img == "None":
                    if verbose:
                        print(colored("ERROR: no image available for " + str(row[1]), "red"))
                    continue
                else:
                    if verbose:
                        print("Image link for " + str(row[1]) + ": " + str(img))
                    cursor.execute("""
                    UPDATE products
                    SET image_link = ?
                    WHERE name = ?
                    """, (str(img), str(row[1])))
                    conn.commit()
            print(colored("Update finished!", "cyan"))
            return 0         
        else:    
            s = requests.Session() #open session
            clean_url = sys.argv[1].partition("?")[0] #remove tracking and unnecessary stuff
            if(not is_link(clean_url)):
                print(colored("ERROR: either a wrong argument or a wrong link was provided", "red"))
                exit(100)
            #we query Amazon regarding the provided link up to MAX_TRIES and we exit only when we get a valid price or we have timed out
            #note that, even if the query does not go through, we allow the script to continue, mostly so that the user can decide whether they want
            #to store the link for later retrievals
            price = 999
            tries = 0
            while price == 999 and tries < MAX_TRIES:
                price, title, img = query_amazon(clean_url, True) #we query Amazon using the query_amazon function
                tries += 1
            if type(price) is not list:
                price = [price]
            #After this, we inquire the database to get the details regarding the requested item.
            #If this query returns something, it means the item already existed in the database, so we need to check whether the price we obtined is lower than the stored one.
            #If it is so, then we need to update it.
            #Else, it means that the item is NOT in the database, hence we need to insert it with its apt metadata
            cursor.execute("SELECT * FROM products WHERE name = ?", (title,))
            result = cursor.fetchone()
            if result:
                if not isinstance(result[2], float):
                    result = list(result)
                    result[2] = float(result[2].replace(",", "."))
                #if price is lower than the stored one...
                if(price[0] != 999):
                    cursor.execute("""
                    INSERT INTO history (product_id, price, timestamp)
                    VALUES (?, ?, ?)
                    """, (result[0], price[0], datetime.datetime.now()))
                if(result[2] > price[0]):
                    #we have got a new lowest price ever for this item...
                    print(colored("New lowest price ever for " + str(title) + "!", "green", attrs=['bold']))
                    #...so we update the database...
                    cursor.execute("""
                    UPDATE products
                    SET price = ?, date = ?
                    WHERE id = ?
                    """, (price[0], datetime.datetime.now(), result[0]))
                    #...and commit the operation
                    conn.commit()
                    print(colored("Updated price for " + str(title) + "!\nOld price: " + str(result[2]) + " - New price: " + str(price[0]), "yellow", attrs=['bold']))
                else:
                    #we provide the user with the lowest ever price seen
                    print(colored("Lowest price ever seen: " + str(result[2]) + "\nSeen on date: " + str(result[3]), "yellow"))
                    if(price[0] != 999):
                        conn.commit()
                return 0
            else:
                #the item we searched for is not in the database...
                if(price[0] == 999):
                    #if the price we got was 999, this means that we were unable to retrieve a price for the given link
                    #Here we ask to the user if it wants to still save the link for future requests or not
                    #If the user chooses no, then we simply exit
                    print(colored("The script was unable to retrieve a price for the given link. Do you still want to save the link?", "red"))
                    terminal_menu = TerminalMenu(["Yes", "No"])
                    menu_entry_index = terminal_menu.show()
                    if(menu_entry_index == 1):
                        exit(1)
                print(price)
                #we insert the item into the database...
                cursor.execute("""
                INSERT INTO products (name, price, date, link, image_link)
                VALUES (?, ?, ?, ?, ?)
                """, (title, price[0], datetime.datetime.now(), clean_url, img))
                #...and commit...
                conn.commit()
                #...and, finally, we print a string for the executed transaction
                print(colored("Inserted a new item in the database!\n Title: " + str(title), "yellow", attrs=['bold']))
                return 0
    elif n == 1:
        #in this case, we simply want to update the prices for the items in the database
        #So what we do is that we get all the items in the products table, query their associated link, call query_amazon, check
        #if the price we obtained was lower than the one we stored and, in that case, we update the item
        print(colored("Updating prices for items in database...", "cyan"))
        updated_titles = []
        updated_prices = []
        if verbose:
            print("Verbose mode active")
        cursor.execute("SELECT * FROM products")
        results = cursor.fetchall()
        for row in results:
            link = row[4]
            price = 999
            tries = 0
            while price == 999 and tries < MAX_TRIES:
                price, title, img = query_amazon(link)
                tries = tries + 1
            if not isinstance(row[2], float):
                row = list(row)
                row[2] = float(row[2].replace(",","."))
            if price == 999:
                continue
            else:
                cursor.execute("""
                    INSERT INTO history (product_id, price, timestamp)
                    VALUES (?, ?, ?)
                    """, (row[0], price[0], datetime.datetime.now()))
                conn.commit()
                if(row[2] > price[0]):
                    print(colored("New lowest price ever for " + str(title) + "!", "green", attrs=['bold']))
                    cursor.execute("""
                    UPDATE products
                    SET price = ?, date = ?
                    WHERE id = ?
                    """, (price[0], datetime.datetime.now(), row[0]))
                    conn.commit()
                    updated_titles.append(title)
                    updated_prices.append(price[0])
                    print(colored("Updated price for " + str(title) + "!\nOld price: " + str(row[2]) + " - New price: " + str(price[0]), "yellow", attrs=['bold']))
                else:
                    print(colored("No price update", "yellow"))
                    print(colored("Lowest price ever seen: " + str(row[2]) + "\nseen on date: " + str(row[3]), "yellow"))
        #at the end of the process, we print the title and the price for those items that we have found a new lowest price
        #if no such object exists, we simply print None and finish executing the script
        print(colored("Elements for which a new lowest ever price was found:", "cyan"))
        if len(updated_titles) != 0:
            for i in range(0, len(updated_titles)):
                print(colored(str(updated_titles[i]) + " - " + str(updated_prices[i]), "magenta"))
        else:
            print(colored("None!", "magenta"))
        print(colored("Update finished!", "cyan"))  
        return 0
    elif n == 3:
        if(sys.argv[1] == "-l"):
            if not os.path.isfile(sys.argv[2]):
                print(colored("ERROR: the provided file does not exist!", "red"))
                exit(10)
            with open(sys.argv[2], 'r') as f:
                lines = f.readlines()
                for line in lines:
                    s = requests.Session() #open session
                    clean_url = line.partition("?")[0] #remove tracking and unnecessary stuff
                    if(not is_link(clean_url)):
                        print(colored("ERROR: either a wrong argument or a wrong link was provided", "red"))
                        continue
                    #we query Amazon regarding the provided link up to MAX_TRIES and we exit only when we get a valid price or we have timed out
                    #note that, even if the query does not go through, we allow the script to continue, mostly so that the user can decide whether they want
                    #to store the link for later retrievals
                    price = 999
                    tries = 0
                    while price == 999 and tries < MAX_TRIES:
                        price, title, img = query_amazon(clean_url, True) #we query Amazon using the query_amazon function
                        tries += 1
                    if type(price) is not list:
                        price = [price]
                    #After this, we inquire the database to get the details regarding the requested item.
                    #If this query returns something, it means the item already existed in the database, so we need to check whether the price we obtined is lower than the stored one.
                    #If it is so, then we need to update it.
                    #Else, it means that the item is NOT in the database, hence we need to insert it with its apt metadata
                    cursor.execute("SELECT * FROM products WHERE name = ?", (title,))
                    result = cursor.fetchone()
                    if result:
                        if not isinstance(result[2], float):
                            result = list(result)
                            result[2] = float(result[2].replace(",", "."))
                        #if price is lower than the stored one...
                        if price[0] != 999:
                            cursor.execute("""
                            INSERT INTO history (product_id, price, timestamp)
                            VALUES (?, ?, ?)
                            """, (result[0], price[0], datetime.datetime.now()))
                        if(result[2] > price[0]):
                            #we have got a new lowest price ever for this item...
                            print(colored("New lowest price ever for " + str(title) + "!", "green", attrs=['bold']))
                            #...so we update the database...
                            cursor.execute("""
                            UPDATE products
                            SET price = ?, date = ?
                            WHERE id = ?
                            """, (price[0], datetime.datetime.now(), result[0]))
                            #...and commit the operation
                            conn.commit()
                            print(colored("Updated price for " + str(title) + "!\nOld price: " + str(result[2]) + " - New price: " + str(price[0]), "yellow", attrs=['bold']))
                        else:
                            #we provide the user with the lowest ever price seen
                            print(colored("Lowest price ever seen: " + str(result[2]) + "\nSeen on date: " + str(result[3]), "yellow"))
                            if(price[0] != 999):
                                conn.commit()
                    else:
                        #the item we searched for is not in the database...
                        if(price[0] == 999):
                            #if the price we got was 999, this means that we were unable to retrieve a price for the given link
                            #Here we ask to the user if it wants to still save the link for future requests or not
                            #If the user chooses no, then we simply exit
                            print(colored("The script was unable to retrieve a price for the given link. Do you still want to save the link?", "red"))
                            terminal_menu = TerminalMenu(["Yes", "No"])
                            menu_entry_index = terminal_menu.show()
                            if(menu_entry_index == 1):
                                exit(1)
                        print(price[0])
                        #we insert the item into the database...
                        cursor.execute("""
                        INSERT INTO products (name, price, date, link, image_link)
                        VALUES (?, ?, ?, ?, ?)
                        """, (title, price[0], datetime.datetime.now(), clean_url, img))
                        #...and commit...
                        conn.commit()
                        #...and, finally, we print a string for the executed transaction
                        print(colored("Inserted a new item in the database!\n Title: " + str(title), "yellow", attrs=['bold']))            
                f.close()
            return 0
        elif(sys.argv[1] == "-d"):
            title = "%" + str(sys.argv[2]) + "%"
            cursor.execute("SELECT * FROM products WHERE name LIKE ?", (title,))
            results = cursor.fetchall()
            result_list = []
            for t in results:
                result_list.append(t[1])
            result_list.append("Do nothing")
            print(colored("Select the item you want to remove from the database: ", "red"))
            terminal_menu = TerminalMenu(result_list)
            menu_entry_index = terminal_menu.show()
            if(menu_entry_index == len(result_list)-1):
                print(colored("Operation aborted!", "red"))
                exit(0)
            else:
                cursor.execute("DELETE FROM history WHERE id = ?", results[menu_entry_index][0])
                cursor.execute("DELETE FROM products WHERE name = ?", (result_list[menu_entry_index],))
                conn.commit()
                print(colored("Selected item successfully deleted!", "cyan"))
                return 0
        elif(sys.argv[1] == "-plt"):
            title = "%" + str(sys.argv[2]) + "%"
            cursor.execute("SELECT * FROM products WHERE name LIKE ?", (title,))
            results = cursor.fetchall()
            result_list = []
            for t in results:
                result_list.append(t[1])
            result_list.append("Do nothing")
            print(colored("Select the item you want the price history plot of: ", "magenta"))
            terminal_menu = TerminalMenu(result_list)
            menu_entry_index = terminal_menu.show()
            if(menu_entry_index == len(result_list)-1):
                print(colored("Operation aborted!", "red"))
                exit(0)
            else:
                cursor.execute("""
                SELECT timestamp, price
                FROM history
                WHERE product_id = ?
                ORDER BY timestamp
                """, (results[menu_entry_index][0],))

                rows = cursor.fetchall()
                if rows:
                    x = list(range(len(rows)))  # numeric axis
                    y = [r[1] for r in rows]

                    labels = [
                        datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m")
                        for r in rows
                    ]

                    plt.clear_data()
                    plt.clear_figure()
                    if(not customized_plot):
                        plt.theme(DEFAULT_THEME)
                        plt.plot(x, y, color=209)
                    else:
                        plt.plot(x, y, color=marker_color)
                        plt.canvas_color(canvas_color)
                        plt.axes_color(axis_color)
                        plt.ticks_color(ticks_color)

                    plt.xticks(x, labels)
                    plt.yticks(y,y)
                    plt.title("Price History for: " + (result_list[menu_entry_index].lstrip() if len(result_list[menu_entry_index].lstrip())<50 else result_list[menu_entry_index].lstrip()[:50]+ "..."))
                    start = max(0, len(x) - 20)
                    end = len(x)

                    plt.xlim(start, end)
                    min_y = min(y)
                    max_y = max(y)

                    if min_y == max_y:
                        margin = 1  # or any fixed padding
                    else:
                        margin = (max_y - min_y) * 0.1
                    plt.ylim(min_y - margin, max_y + margin)
                    plt.xlabel("Time")
                    plt.ylabel("Price")
                    plt.plotsize(100, 20)

                    plt.show()
                    
                    return 0
                else:
                    print(colored("ERROR: no informatiomn available for the selected item!", "red")) 
                    exit(20)        
        else:
            print(colored("ERROR: provided wrong flag to the script", "red"))
            exit(4)
    else:
        print_usage()
        return 0      

if __name__ == "__main__":
    main()