#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import sys
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for

from datetime import date, timedelta
from env_variables import log_in_username, log_in_password


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = log_in_username
DB_PASSWORD = log_in_password

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


LOGGED_IN_AS = None
LOGGED_IN_EMAIL = None

@app.before_request
def before_request():
    """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)


    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT name FROM test")
    names = []
    for result in cursor:
        names.append(result['name'])  # can also be accessed using result[0]
    cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
    context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
    return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
    
    return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    print(name)
    cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
    g.conn.execute(text(cmd), name1 = name, name2 = name);
    return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

@app.route('/home')
def home():

    data = load_data_for_user(LOGGED_IN_AS)
    data.update(username_welcome = LOGGED_IN_AS, 
                    today = date.today().strftime("%B %d, %Y"))

    return render_template("home.html", **data)

@app.route('/inventory')
def inventory():
    
    data = load_data_for_user(LOGGED_IN_AS, going_bad_soon = False)
    
    return render_template("inventory.html", **data)
    
@app.route('/preferences')
def preferences():
    
    data = load_data_for_user(LOGGED_IN_AS, going_bad_soon = False)
    data = get_allergies(data, LOGGED_IN_AS)
    return render_template("preferences.html", **data)

@app.route('/recipes')
def recipes():
    
    data = dict()
    data = load_recipe_data(data, LOGGED_IN_AS, going_bad_soon = False)
    
    return render_template("recipes.html", **data)
    
@app.route('/reviews')
def reviews():
    
    data = load_data_for_user(LOGGED_IN_AS, going_bad_soon = False)
    data = users_reviews(data)
    data = recipes_list(data)
    return render_template("reviews.html", **data)


@app.route('/display_recipe', methods=['GET', 'POST'])
def display_recipe():
    recipe_name = request.args.get('type')
    
    data = load_recepe(recipe_name)
    
    return render_template("display_recipe.html", **data)
    
    
@app.route('/signup')
def signup():
    data = load_data_for_user(LOGGED_IN_AS, going_bad_soon=False)
    return render_template("signup.html", **data)


@app.route('/signout')
def signout():
    global LOGGED_IN_AS
    LOGGED_IN_AS = None
    global LOGGED_IN_EMAIL
    LOGGED_IN_EMAIL = None
    return render_template("index.html")

@app.route('/app', methods=['POST'])
def login_server():
    #abort(401)
    #this_is_never_executed()
    
    # Example: username: WHo, password: 1234
    try:
        username = request.form['uname']
        password = request.form['passw']
    except:
        return render_template("index.html", wrong_password = 'Wrong credentials, please try again.')
    
    query = """
    SELECT *
    FROM users
    WHERE username = (%s) AND password = (%s)
    """
    
    cursor = g.conn.execute(query, (username, password))
    
    res = cursor.all()
    cursor.close()
    if len(res) > 0:
        global LOGGED_IN_AS
        global LOGGED_IN_EMAIL
        LOGGED_IN_AS = res[0][0]
        LOGGED_IN_EMAIL = res[0][1]
        
        data = load_data_for_user(LOGGED_IN_AS)

        data.update(username_welcome = LOGGED_IN_AS, 
                    today = date.today().strftime("%B %d, %Y"))

        return render_template("home.html", **data)
    
    return render_template("index.html", wrong_password = 'Wrong credentials, please try again.')

def run_query_and_return_all(query, params):
    cursor = g.conn.execute(query, params)
    
    ret_values = cursor.all()
    cursor.close()
    
    return ret_values

def load_ingredients_in_inventory(data, username, going_bad_soon = True):
    
    query = """
    SELECT ich.ingredient_id, expiration_date, quantity, description, calories
    FROM Inventory_currently_has as ich
    INNER JOIN Ingredient as i ON (i.ingredient_id = ich.ingredient_id)
    WHERE username = (%s)
    """
    
    ingredients = run_query_and_return_all(query, (username))
    going_bad_soon_list = []
    going_bad_ingredient_id = []
    ret_ing = []
    for ing in ingredients:
        ing = dict(ing)
        if going_bad_soon:
            if ing['expiration_date'] < date.today() + timedelta(7):
                ing['expiration_date'] = ing['expiration_date'].strftime("%B %d, %Y")
                going_bad_soon_list.append(ing)
                going_bad_ingredient_id.append((ing['ingredient_id'], ing['expiration_date']))
            else:
                ing['expiration_date'] = ing['expiration_date'].strftime("%B %d, %Y")
        else:
            ing['expiration_date'] = ing['expiration_date'].strftime("%B %d, %Y")
            going_bad_soon_list.append(ing)
            going_bad_ingredient_id.append((ing['ingredient_id'], ing['expiration_date']))
                
        ret_ing.append(ing)
    
    data.update(ingredients = ret_ing, going_bad_soon = going_bad_soon_list)
    
    going_bad_ingredient_id = sorted(going_bad_ingredient_id, key=lambda tup: tup[1])

    going_bad_ingredient_ids = [i[0] for i in going_bad_ingredient_id]
    going_bad_ingredient_dates = [i[1] for i in going_bad_ingredient_id]
    
    return data, going_bad_ingredient_ids, going_bad_ingredient_dates
    
def current_inventory_satisfies(data, username, going_bad_soon_list, going_bad_soon_dates, consider_alergies = True):
    
    if consider_alergies:
        query = """
        SELECT available_recipies.recipe_name, ri2.ingredient_id, i2.description
        FROM (
        SELECT ri.recipe_name, ui.username
        FROM Inventory_currently_has as uch
        INNER JOIN Users_Inventory as ui ON (uch.inventory_id = ui.inventory_id)
        INNER JOIN Recipe_ingredients as ri ON (ri.ingredient_id = uch.ingredient_id)
        WHERE ui.username = (%s)
        GROUP BY ui.username, ri.recipe_name
        HAVING COUNT(ri.ingredient_id) = (
          SELECT COUNT(*)
          FROM Recipe_ingredients as inn_ri
          WHERE inn_ri.recipe_name = ri.recipe_name
        )
        ) as available_recipies
        INNER JOIN Recipe_ingredients as ri2 ON (ri2.recipe_name = available_recipies.recipe_name)
        INNER JOIN Ingredient as i2 ON (ri2.ingredient_id = i2.ingredient_id)
        WHERE available_recipies.recipe_name not in (
            select ri.recipe_name
            from  Allergy_examples as ae
            inner join Users_allergies as ua on (ae.allergy_type = ua.allergy_type)
            inner join Recipe_ingredients as ri on (ri.ingredient_id = ae.ingredient_id)
            where  ua.username = available_recipies.username
        )
    """
    else:
        query = """
        SELECT available_recipies.recipe_name, ri2.ingredient_id, i2.description
        FROM (
        SELECT ri.recipe_name
        FROM Inventory_currently_has as uch
        INNER JOIN Users_Inventory as ui ON (uch.inventory_id = ui.inventory_id)
        INNER JOIN Recipe_ingredients as ri ON (ri.ingredient_id = uch.ingredient_id)
        WHERE ui.username = (%s)
        GROUP BY ui.username, ri.recipe_name
        HAVING COUNT(ri.ingredient_id) = (
          SELECT COUNT(*)
          FROM Recipe_ingredients as inn_ri
          WHERE inn_ri.recipe_name = ri.recipe_name
        )
        ) as available_recipies
        INNER JOIN Recipe_ingredients as ri2 ON (ri2.recipe_name = available_recipies.recipe_name)
        INNER JOIN Ingredient as i2 ON (ri2.ingredient_id = i2.ingredient_id)
        """
    cursor = g.conn.execute(query, (username))
    
    recipes = set()
    prio_dict = dict()

    for res in cursor:
        recipes.add(res['recipe_name'])
        for i, zi in enumerate(zip(going_bad_soon_list, going_bad_soon_dates)):
            red_id, re_date = zi
            if res['ingredient_id'] == red_id:
                res = dict(res)
                res['exp_date'] = re_date
                if i in prio_dict.keys():
                    prio_dict[i].append(res)
                else:
                    prio_dict[i] = [res]
                break
        
    cursor.close()
    prio_dict = dict(sorted(prio_dict.items()))
    prio_recipes = dict()

    for k, v in prio_dict.items():
        for res in v:
            if res['description']+': '+res['exp_date'] not in prio_recipes.keys():
                prio_recipes[res['description']+': '+res['exp_date']] = [res['recipe_name']]
            else:
                prio_recipes[res['description']+': '+res['exp_date']].append(res['recipe_name'])
    
    data.update(currently_available_recipies = recipes, prio_recipes = prio_recipes)

    return data

def load_data_for_user(username, going_bad_soon = True):
    
    data = dict()
    
    data, going_bad_ingredient_id, going_bad_ingredient_dates = load_ingredients_in_inventory(data, username, going_bad_soon =going_bad_soon)
    data = current_inventory_satisfies(data, username, going_bad_ingredient_id, going_bad_ingredient_dates)
    
    
    return data
    
    
    
    
@app.route('/add_item_to_inventory', methods=['POST'])
def add_items_to_inventory():
    
    try:
        item = request.form['itemname']
        quantity = int(request.form['quantity'])
        exp_date = request.form['exp_date']
        calories = request.form['calories']
    except:
        exp_date = None
        calories = 0
        
    find_item_query = """
    SELECT ingredient_id
    FROM Ingredient
    WHERE description = (%s)
    """
    
    cursor = g.conn.execute(find_item_query, item)
    
    if cursor.rowcount < 1:
        new_ing_id_query = """
        SELECT MAX(ingredient_id)
        FROM Ingredient
        """
        cursor_2 = g.conn.execute(new_ing_id_query)
        ingredient_id = cursor_2.first()[0] + 1
        cursor_2.close()
        
        insert_new_ingredient = """
        iNSERT INTO Ingredient (ingredient_id, description, calories) VALUES
            ((%s), (%s), (%s))
        """
        if not calories:
            calories = 0
        cursor_3 = g.conn.execute(insert_new_ingredient, (ingredient_id, item, calories))
        cursor_3.close()
    else:
        ingredient_id = cursor.first()[0]
    
    cursor.close()
    
    user_inventory_query = """
    SELECT inventory_id
    FROM Users_Inventory
    WHERE username = (%s)
    """
    user_inventory_cursor = g.conn.execute(user_inventory_query, LOGGED_IN_AS)
    inventory_id = user_inventory_cursor.first()[0]
    user_inventory_cursor.close()
    
    insert_item_query = """
    INSERT INTO Inventory_currently_has VALUES
    ((%s), (%s), (%s),  (%s), (%s))
    """
    try:
        insert_cursor = g.conn.execute(insert_item_query, (inventory_id, LOGGED_IN_AS, ingredient_id, exp_date, quantity))
        insert_cursor.close()
    except:
        pass

    
    return redirect('/inventory')
    
@app.route('/remove_item_from_inventory', methods=['POST'])
def remove_item_from_inventory():
    
    ing_id = int(request.form['delete_invent_item'])
    del_query = """
    DELETE
    FROM Inventory_currently_has
    WHERE ingredient_id=(%s) AND username = (%s)
    """
    del_cursor = g.conn.execute(del_query, (ing_id, LOGGED_IN_AS))
    del_cursor.close()
    
    return redirect('/inventory')


def users_reviews(data):
    user_reviews_query = """
    SELECT rr.recipe_name, rw.stars, rw.review_text, rw.review_id
    FROM Review_written_by rwb, Review rw, Review_of_recipe rr
    WHERE rwb.username = (%s)
    AND rw.review_id = rwb.review_id
    AND rw.review_id = rr.review_id
    """
    cursor = g.conn.execute(user_reviews_query, LOGGED_IN_AS)
    reviews_list = []
    for res in cursor:
        reviews_list.append([res['recipe_name'], res['stars'], res['review_text'], res['review_id']])
    cursor.close()
    data.update(reviews=reviews_list)
    return data


def recipes_list(data):
    recipes_query = """
    SELECT recipe_name FROM Recipe ORDER BY recipe_name
    """
    cursor = g.conn.execute(recipes_query)
    recipes_list = []
    for res in cursor:
        recipes_list.append(res['recipe_name'])
    cursor.close()
    data.update(recipes_list=recipes_list)
    return data


@app.route('/add_review', methods=['POST'])
def add_review():
    recipe_name = request.form['recipe']
    stars = int(request.form['rating'])
    review_text = request.form['review_text']

    # Check if this user has already made a review for recipe_name
    check_query = """
    SELECT rw.review_id
    FROM Review_written_by rwb, Review rw, Review_of_recipe rr
    WHERE rwb.username = (%s)
    AND rw.review_id = rwb.review_id
    AND rw.review_id = rr.review_id
    AND rr.recipe_name = (%s)
    """
    cursor0 = g.conn.execute(check_query, (LOGGED_IN_AS, recipe_name))
    res = cursor0.all()
    cursor0.close()
    if len(res) > 0:
        data = {'username': LOGGED_IN_AS}
        data = load_data_for_user(LOGGED_IN_AS, going_bad_soon = False)
        data = users_reviews(data)
        data = recipes_list(data)
        data.update(wrong_input='You have already reviewed this recipe!')
        return render_template("reviews.html", **data)

    # Add review
    review_id_query = """
    SELECT MAX(review_id)
    FROM Review
    """
    cursor1 = g.conn.execute(review_id_query)
    rev_id = cursor1.first()[0] + 1
    cursor1.close()
    add_review_query = """
    INSERT INTO Review VALUES
    ((%s), (%s), (%s))
    """
    cursor2 = g.conn.execute(add_review_query, (rev_id, stars, review_text))
    cursor2.close()
    add_review_written_query = """
    INSERT INTO Review_written_by VALUES
    ((%s), (%s))
    """
    cursor3 = g.conn.execute(add_review_written_query, (LOGGED_IN_AS, rev_id))
    cursor3.close()
    add_review_of_query = """
    INSERT INTO Review_of_recipe VALUES
    ((%s), (%s))
    """
    cursor4 = g.conn.execute(add_review_of_query, (recipe_name, rev_id))
    cursor4.close()
    return redirect('/reviews')


@app.route('/delete_review', methods=['POST'])
def delete_review():
    rev_id = int(request.form['delete_review'])
    del_query = """
    DELETE FROM Review_written_by WHERE review_id=(%s);
    DELETE FROM Review_of_recipe WHERE review_id=(%s);
    DELETE FROM Review WHERE review_id=(%s)
    """
    del_cursor = g.conn.execute(del_query, (rev_id, rev_id, rev_id))
    del_cursor.close()
    return redirect('/reviews')


@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        username = request.form['uname']
        email = request.form['email']
        password = request.form['passw']
    except:
        return render_template("signup.html", wrong_password='Invalid entry, please try again.')
    check_query = """
    SELECT *
    FROM Users
    WHERE username = (%s) OR email = (%s)
    """
    cursor = g.conn.execute(check_query, (username, email))
    res = cursor.all()
    cursor.close()
    if len(res) > 0:
        return render_template("signup.html", wrong_password='Username and/or email already in use.')
    else:
        insert_query = """
        INSERT INTO Users VALUES
        ((%s), (%s), (%s))
        """
        cursor = g.conn.execute(insert_query, (username, email, password))
        cursor.close()
    return render_template("signup.html", wrong_password='Sign Up Successful!')
    
def load_recipe_data(data, username, going_bad_soon = False):
    
    recipe_query = """
    SELECT recipe_name
    FROM Recipe    
    ORDER BY recipe_name
    """
    
    recipe_cursor = g.conn.execute(recipe_query)
    rec_names = []
    for res in recipe_cursor:
        rec_names.append(res['recipe_name'])
    
    recipe_cursor.close()
    
    data.update(rescipes = rec_names)
    
    return data


def load_recepe(recipe_name):
    
    recipe_ingredient_query = """
    SELECT r.recipe_name, ri.ingredient_id, i.description, ich.expiration_date
    FROM Recipe as r
    INNER JOIN Recipe_ingredients as ri ON (r.recipe_name = ri.recipe_name)
    INNER JOIN Ingredient as i ON (ri.ingredient_id = i.ingredient_id)
    LEFT JOIN (
    SELECT *
    FROM Inventory_currently_has iii
    WHERE iii.username = (%s)
    ) as ich
    ON (ri.ingredient_id = ich.ingredient_id)
    WHERE r.recipe_name = (%s)
    """
    
    rec_ing_cursor = g.conn.execute(recipe_ingredient_query, (LOGGED_IN_AS, recipe_name))
    ret_ing = rec_ing_cursor.all()
    rec_ing_cursor.close()
    
    recipie_inst_query =  """
    SELECT r.recipe_name, r.instructions, AVG(stars) as avg_star
    FROM Recipe as r
    LEFT JOIN Review_of_recipe as ror ON (r.recipe_name = ror.recipe_name)
    LEFT JOIN Review as re ON (ror.review_id = re.review_id)
    WHERE r.recipe_name = (%s)
    GROUP BY r.recipe_name, r.instructions
    """
    rec_inst_cursor = g.conn.execute(recipie_inst_query, (recipe_name))
    ret = rec_inst_cursor.first()
    inst_display = []
    try:
        ret_inst = ret[1]
        inst_display = ret_inst.split('\\n')
        if len(inst_display) == 1:
            inst_display = inst_display[0].split('\n')
        ret_stars = round(ret[2], 1)
    except:
        if not inst_display:
            inst_display = []
        ret_stars = "N/A"
    
    rec_inst_cursor.close()
    
    review_query =  """
    SELECT stars, review_text, username
    FROM Review_of_recipe as r
    inner join Recipe as re ON(r.recipe_name = re.recipe_name)
    INNEr JOIN Review rev on (rev.review_id = r.review_id)
    inner join Review_written_by rb on (rb.review_id = r.review_id)
    wHERE re.recipe_name = (%s)
    """
    
    review_ret = g.conn.execute(review_query, recipe_name)
    reviews = []
    
    for rev_res in review_ret:
        reviews.append({
            'username': rev_res['username'],
            'rev_text': rev_res['review_text'],
            'stars': rev_res['stars']
        }
    )
    
    
    data = dict(recipe_ing = ret_ing, instruction = inst_display, recipe_name = recipe_name, avg_star = ret_stars, review_text = reviews)

    return data


def get_user_allergies(username):
    # Get allergy types and descriptions for things the user is allergic to
    user_allergies_query = """
        SELECT a.allergy_type
        FROM Users_allergies ua, Allergies a
        WHERE ua.username = (%s)
        AND ua.allergy_type = a.allergy_type
        ORDER BY a.allergy_type DESC
        """
    cursor = g.conn.execute(user_allergies_query, username)
    user_allergies = []
    for res in cursor:
        user_allergies.append(res['allergy_type'])
    cursor.close()
    return user_allergies


def get_allergies(data, username):
    user_allergies = get_user_allergies(username)
    all_allergies_query = """
    SELECT a.allergy_type, a.description
    FROM Allergies a
    ORDER BY a.allergy_type DESC
    """
    cursor = g.conn.execute(all_allergies_query)
    allergies = []
    for res in cursor:
        allergic_to = False
        if res['allergy_type'] in user_allergies:
            allergic_to = True
        allergies.append({
            'allergy_type': res['allergy_type'],
            'allergy_desc': res['description'],
            'allergic_to': allergic_to})
    cursor.close()
    data.update(allergies=allergies)
    return data


@app.route('/change_user_allergy', methods=['POST'])
def change_user_allergy():
    toggled_on = request.form.getlist('allergen')
    user_allergies = get_user_allergies(LOGGED_IN_AS)
    all_allergies_query = """
    SELECT a.allergy_type
    FROM Allergies a
    ORDER BY a.allergy_type DESC
    """
    cursor = g.conn.execute(all_allergies_query)
    for res in cursor:
        all_type = res['allergy_type']
        if all_type in user_allergies and all_type in toggled_on:
            # Do nothing
            continue
        elif all_type in user_allergies and all_type not in toggled_on:
            # DELETE Allergy
            query = """
            DELETE FROM Users_allergies
            WHERE username=(%s)
            AND allergy_type=(%s)
            """
            cursor1 = g.conn.execute(query, (LOGGED_IN_AS, all_type))
            cursor1.close()
        elif all_type not in user_allergies and all_type in toggled_on:
            # Add Allergy
            query = """
            INSERT INTO Users_allergies VALUES
            ((%s), (%s))
            """
            cursor1 = g.conn.execute(query, (LOGGED_IN_AS, all_type))
            cursor1.close()
        else:
            # Do nothing
            continue
    cursor.close()
    return redirect('/preferences')


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using

            python server.py

        Show the help text using

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
