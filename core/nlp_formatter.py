# General imports
import json
import re
import string
import requests
from difflib import SequenceMatcher
from numpy import mean
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


# -------------- Getting required files ---------------


def get_ingredients_collection():
    response = requests.get(
        'https://stayingvegan.co/ingredients.txt')
    data = response.json()
    ingredients_collection = data['ingredients_collection']
    return ingredients_collection


def get_ingredient_list():
    response = requests.get(
        'https://stayingvegan.co/ingredients_list.txt')
    data = response.json()
    ingredient_list = data['ingredient_list']
    return ingredient_list


def ingredient_search():
    response = requests.get(
        'https://stayingvegan.co/ingredient_search.txt')
    data = response.json()
    ingredient_list = data['ingredient_list']
    return ingredient_list


def get_recommended_nutrition():
    response = requests.get(
        'https://stayingvegan.co/firestore_nutrition.txt')
    rec_nutrition = response.json()
    return rec_nutrition


def get_nutrients_from_firestore():
    response = requests.get(
        'https://stayingvegan.co/nutrient_list.txt')
    nutrient_list = response.json()
    return nutrient_list


# ---------------- NLP formatting ---------------


def lemmatizeIngredient(ingredient):
    ''' Gets the singular of each word '''
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(ingredient)

    lemmatized_words = []
    for word in words:
        lemmatized_words.append(lemmatizer.lemmatize(word, pos='v'))

    ingredient = " ".join(lemmatized_words)

    return ingredient


def remove_accents_and_symbols(ingredient):
    ''' Remove symbols '''
    ing = ingredient
    ing = ing.replace(' and', '')
    ing = ing.replace('ā', 'a')
    ing = ing.replace('ç', 'c')
    ing = ing.replace('ó', 'o')
    ing = ing.replace('è', 'e')
    ing = ing.replace('é', 'e')
    ing = ing.replace('ō', 'o')
    ing = ing.replace('ú', 'u')
    ing = ing.replace('î', 'i')
    ing = ing.replace('í', 'i')
    ing = ing.replace('ñ', 'n')
    ing = ing.replace('®', '')
    ing = ing.replace('™', '')

    return ing

# Removes general and recipe specific stop words


def remove_stopwords(ingredient):
    ''' Remove stop words to improve classification '''
    general_stop_words = stopwords.words('english')
    cooking_stop_words = ['finely', 'chopped', 'piece', 'choice', 'favourite', 'read', 'my', 'your'
                          'here', 'find', 'recipe', 'also', 'work', 'diced', 'very', 'small', 'medium', 'large',
                          'desired', 'needed', 'ripe', 'raw', 'halved', 'flavourful', 'worth', 'see', 'above',
                          'roughly', 'add', 'ins', 'use', 'small-medium', 'approx', 'approximately', 'juice', 'zest']

    words = word_tokenize(ingredient)
    stripped_ingredient = []
    for word in words:
        if word not in general_stop_words:
            if word not in cooking_stop_words:
                stripped_ingredient.append(word)
            else:
                None

    ingredient = " ".join(stripped_ingredient)

    return ingredient



def ingredient_pre_cleanse(ingredient):
    ingredient = ingredient.lower()
    # Remove anything inside brackets
    ingredient = re.sub("[\(\[].*?[\)\]]", "", ingredient)
    # Remove double spacing
    ingredient = ingredient.replace('  ', ' ')
    # Remove optional and colon
    ingredient = ingredient.replace('optional', '')
    ingredient = ingredient.replace(':', '')

    return ingredient


# -------------- Formatting quantities and units ------------

# Gets the quantity from the ingredient
def get_quantity(remaining_string):
    ''' Get quantity from the remaining string '''
    unicode = ['½', '¼', '¾', '⅓', '⅛']

    # Some pre cleaning
    remaining_string = remaining_string.replace('juice', ' ')

    # Remove numbers from the end of the sting
    ingredient = remaining_string

    # Srtip space from either side
    ingredient = ingredient.strip()

    # Remove leading 1's
    try:
        if ingredient[0] == '1' and ingredient[1] == ' ' and ingredient[2].isdigit() and ingredient[3] != '/':
            ingredient = ingredient[2:]

        elif ingredient[0] == '1' and ingredient[1] == 'x':
            ingredient = ingredient[2:]
    except:
        None

    # Scenario 0 - if the quantity should be multiplied but no 'x'
    try:
        if ingredient[1] == ' ' and ingredient[0].isdigit() and ingredient[2:3].isdigit():
            # Split the string and multiply the quantities
            ingredient = ingredient.replace('-', ' ')
            ingredient_split = ingredient.split(' ')
            ingredient = int(ingredient_split[0]) * int(ingredient_split[1])
            # Remove the rest of the ingredient so the following line will only take the digit
            ingredient = str(ingredient)

    except:
        None

    # If theres just one number at the start then take that
    if re.match('^\d*[.,]?\d*$', ingredient):
        quantity = ingredient

    else:

        # Find the string after the 1/4th quantity should be at the start, numbers after this cause issues
        length = int(len(ingredient))
        quarter = int(length / 4)

        if len(ingredient) > 12:
            quarter_string = ingredient[quarter:]
            for index, e in enumerate(quarter_string):
                if (index + 1 < len(ingredient) and index - 1 >= 0):
                    if e.isdigit():
                        ingredient = ingredient[:quarter] + \
                            quarter_string[:index - 1] + \
                            quarter_string[index + 1:]

        # Scenario 1. Dealing with quantity are multiplied (e.g 2 x 400g cans)
        # If the string contains an 'x' multipy the two numbers (if 5th index is digit)
        if ' x ' in ingredient[:4] and ingredient[4].isdigit():
            try:
                ingredient = ingredient.split(' x ')
                # print(ingredient)
                if ingredient[0] == '¼':
                    ingredient[0] = float(0.25)
                elif ingredient[0] == '½':
                    ingredient[0] = float(0.5)
                else:
                    ingredient[0] = ingredient[0]
                    ingredient = list(filter(None, ingredient))

            except Exception as e:
                pass

            try:
                ingredient[1] = re.split('(\d+)', ingredient[1], 2)
                number = float(ingredient[0])
                size = float(ingredient[1][1])
                quantity = number * size
                # print('Quantity has been multiplied')
                ingredient = ingredient[-1]
            except:
                ingredient = ingredient
                quantity = 0

        else:
            ingredient = ingredient
            quantity = None

        # Scenario 2. Dealing with fractions and multiplications together (e.g. 2 x 1/4)
        if len(ingredient) > 5:
            if 'x' in ingredient[:4] and ingredient[5] == '/':
                try:
                    if '1/2' in ingredient[:5]:
                        fraction = float(0.5)
                    elif '1/3' in ingredient[:5]:
                        fraction = float(0.33)
                    elif '3/4' in ingredient[:5]:
                        fraction = float(0.66)

                    number = float(ingredient[0])
                    quantity = number * fraction

                except:
                    quantity = 0

            else:
                ingredient = ingredient
                quantity = None

        # Scenario 3. If whole number and a fraction with a space inbetween (e.g. 2 1/2')
        try:
            if ingredient[3] == '/' and ingredient[1] == ' ':
                try:
                    if '1/2' in ingredient[:5]:
                        fraction = float(0.5)
                    elif '1/3' in ingredient[:5]:
                        fraction = float(0.33)
                    elif '3/4' in ingredient[:5]:
                        fraction = float(0.66)
                    whole = float(ingredient[0])
                    quantity = whole + fraction
                except:
                    None
            else:
                ingredient = ingredient
                quantity = 0
        except:
            None

        # Scenario 4. If the string contains a range indicated by 'to', convert it to a '-'
        if ' to ' in ingredient[:6]:
            try:
                ingredient = ingredient.replace(' to ', '-')
            except:
                ingredient = ingredient

        # Remove the section before the '/' if theres no digit
        if '/' in ingredient[:4] and not ingredient[0].isdigit():
            try:
                ingredient = ingredient.split('/')[1]
            except:
                None
        else:
            ingredient = ingredient

        # Scenario 5. If the string has two quantities and units (e.g. 2 cups / 100g)
        # Remove the first,  but ignore if it contains a non digit
        if '/' in ingredient[:5] and ingredient[0].isdigit() and not [i.isdigit() for i in ingredient[:3]]:
            ingredient = ingredient.split('/')
            if not ingredient[0][-1].isdigit():
                ingredient = ingredient[1]
        else:
            ingredient = ingredient

        # Scenario 6. The quantity is just a fraction.
        # Split on the the first 2 digits if there is a fraction in the quantity
        if '/' in ingredient[:3] and ingredient[0].isdigit():
            try:
                ingredient = re.split('(\d+)', ingredient, 2)
                ingredient = re.split('')

            except:
                None

        # Scenario 7. The quantity is in a range (e.g. 1-2 tsp)
        # Split on the the first 2 digits an
        elif '-' or '–' or '–' in ingredient[:3]:
            try:
                ingredient = re.split('(\d+)', ingredient, 2)
                ingredient = re.split('')

            except:
                None

        # Else split on the first digit of the ingredient
        else:

            try:
                ingredient = re.split('\d*\.?\d+', ingredient, 1)
                ingredient = re.split('')

            except:
                None

        # Remove empty remaining strings from the split list
        ingredient = list(filter(None, ingredient))

        # Get the Quantity

        # Try to get the quantity if its just a number
        if quantity == None:
            try:
                quantity = re.findall('\d*\.?\d+', ingredient)
            except:
                quantity = None

        # Else if the quantity is a different format
        elif quantity == 0:
            try:

                # If ingredient is a decimal
                if ingredient[1] == '.':
                    quantity = " ".join(ingredient[:3])
                    quantity = quantity.replace(' ', '')

                # If quantity is a fraction - takes the '/' and adds fraction to quantity
                elif ingredient[1] == '/':
                    quantity = ingredient[0] + ingredient[1] + ingredient[2]

                elif ingredient[1] == '-':
                    quantity = float(ingredient[0])

                # If the quantity is a whole number and  a unicode - convert it accordingly
                elif ingredient[1][0] in unicode:
                    quantity = ingredient[0][0] + ingredient[1][0]

                    if '1' and '½' and not '2' in quantity:
                        quantity = float(1.5)

                    elif '2' and '½' and not '1' in quantity:
                        quantity = float(2.5)

                elif ingredient[1][1] in unicode:
                    quantity = ingredient[0][0] + ingredient[1][1]

                    if '1' and '½' and not '2' in quantity:
                        quantity = float(1.5)

                    elif '2' and '½' and not '1' in quantity:
                        quantity = float(2.5)

                # If the quantity is not a fraction then the quantity remains the same but is changed to float.
                else:
                    for q in ingredient[0]:
                        if q.isdigit():
                            quantity = ingredient[0]
                            quantity = float(quantity)
                        else:
                            quantity = ingredient[1]

            # If quanitity is unicode convert it accordingly to fraction
            except:

                try:

                    if ingredient[0][0] == '½':
                        quantity = '1/2'
                    elif ingredient[0][0] == '¼':
                        quantity = '1/4'
                    elif ingredient[0][0] == '¾':
                        quantity = '3/4'
                    elif ingredient[0][0] == '⅓':
                        quantity = '1/3'
                    elif ingredient[0][0] == '⅛':
                        quantity = '1/8'
                    elif ingredient[0][0] == '⅔':
                        quantity = '2/3'

                    else:
                        quantity = None
                except:
                    ingredient = ingredient

            # Then convert all of the fractions to floats
            if quantity == '1/2':
                quantity = float(0.5)
            if quantity == '3/8':
                quantity = float(0.375)
            elif quantity == '1/3':
                quantity = float(0.33)
            elif quantity == '1/4':
                quantity = float(0.25)
            elif quantity == '3/4':
                quantity = float(0.75)
            elif quantity == '1/8':
                quantity = float(0.125)
            elif quantity == '2/3':
                quantity = float(0.66)
            else:
                try:
                    quantity = float(quantity)
                except:
                    quantity = None

        # One last catch for some quantities that have been split.
        if quantity == None:
            if ingredient[0].isdigit():
                quantity = ingredient[0]
            else:
                quantity = None

    # Standardise format
    try:
        quantity = float(quantity)
    except:
        quantity = None

    # If quantity is still none, look for string quantities
    if quantity == None:

        try:
            # Convert words to float
            if 'half' in ingredient[0]:
                quantity = 0.5

            if 'quarter' in ingredient[0]:
                quantity = 0.25

            if 'third' in ingredient[0]:
                quantity = 0.33

        except:
            None

    # Return to master function
    return quantity

# Gets the units from the ingredient


def get_unit(remaining_string):
    measurement_units = ['tsp', 'teaspoon', 'teaspoons', 'tsp.', 'tsps',
                         'tbsp', 'tablespoon', 'tablespoons', 'tbs', 'tb', 'tbsp.', 'tbsps',
                         'c', 'cup', 'cups',
                         'ml', 'milliliters', 'millilitres', 'mls',
                         'pt', 'pint', 'pints', 'l', 'liter', 'litre', 'litres', 'liters', 'dl', 'dash', 'dashes',
                         'oz', 'ounce', 'ounces', 'pkg',
                         'g', 'gram', 'grams', 'mg', 'mgs',
                         'gallon', 'gallons', ' gal', 'gals', 'gill', 'gills', 'gl', 'fl. oz', 'fl.oz',
                         'lb', 'lbs', 'pound', 'pounds',
                         'mm ', "mm's", 'millimetres', 'millimeters', 'centimetre', 'centimeters', 'cm', "cm's", 'kg ', ' kg',
                         'inches', 'inch', 'heapings', 'heaping', 'pinch', 'pinches', 'taste', 'garnish', 'serve', 'stalk', 'sprinkle',
                         'qt', 'quart.', 'tin', 'tins', 'jar', 'jars', 'pots', 'can', 'cans', 'carton', 'cartons', 'packets', 'pack', 'package',
                         'dollop', 'dollops', 'slice', 'slices', 'handful', 'handfuls', 'block', 'blocks', 'sackets', 'packages', 'bunch', 'box', 'wedges',
                         'sprigs', 'sprig', 'cloves', 'clove', 'bulb', 'head', 'bulbs', 'bunch', 'packet', 'packets', 'rib', 'ribs', 'scoop', 'drops', 'shot']

    # Split the string to find the measurement units
    string_split = remaining_string.split()

    # Loop through the list of units. This will find the first unit and then break the loop
    unit_match = False

    for i in string_split:
        for x in measurement_units:
            if i == x:
                measurement_unit = i

                unit_match = True
                break
            else:
                unit_match = False

        if unit_match == True:
            break

    measurements_to_exclude = ['l', 'c', 'slice',
                               'g', 'pt', 'gl', 'tin', 'oz', 'dl']

    # Else check the string again incase it hasnt been split
    if unit_match == False:
        for x in measurement_units:
            if x in remaining_string and x not in measurements_to_exclude:  # Exclude x as it picks up letters
                measurement_unit = x
                unit_match = True
                break

            else:
                unit_match = False
                measurement_unit = None

    return measurement_unit

# Removes units from the string after they have been found


def remove_units(remaining_string):
    measurement_units = ['tsp', 'teaspoon', 'teaspoons', 'tsp.', 'tsps',
                         'tbsp', 'tablespoon', 'tablespoons', 'tbs', 'tb', 'tbsp.', 'tbsps',
                         'c', 'cup', 'cups',
                         'ml', 'milliliters', 'millilitres', 'mls',
                         'pt', 'pint', 'pints', 'l', 'liter', 'litre', 'litres', 'liters', 'dl', 'dash', 'dashes',
                         ' oz', 'ounce', 'ounces',
                         'g ', ' g', '.g', 'gram', 'grams', 'mg', 'mgs', 'kg',
                         'gallon', 'gallons', ' gal', 'gals', 'gill', 'gills', 'gl', 'fl. oz', 'fl.oz',
                         'lb', 'lbs', 'pound', 'pounds',
                         'mm', "mm's", 'millimetres', 'millimeters', 'centimetre', 'centimeters', 'cm', "cm's",
                         'inches', 'inch', 'heapings', 'heaping', 'pinch', 'pinches', 'to taste', 'to garnish', 'to serve', 'stalk',
                         'qt', 'quart.', 'tin', 'tins', 'jar', 'jars', 'pot', 'pots', 'can', 'cans', 'carton', 'cartons', 'packets', 'pack',
                         'dollop', 'dollops', 'slice', 'slices', 'handful', 'handfuls', 'block', 'blocks', 'sackets', 'packages', 'bunch',
                         'sprigs', 'sprig', 'cloves', 'clove', 'bulb', 'head', 'bulbs', 'bunch', 'packet', 'packets', 'rib', 'ribs']

    string_split = remaining_string.split()

    for i in string_split:
        for x in measurement_units:
            if i == x:
                remaining_string = remaining_string.replace(x, ' ')
                break

    return remaining_string

# Converts units into a standardised format


def convert_units(measurement_unit):
    unit = measurement_unit
    if unit == 'tablespoons' or unit == 'tablespoon' or unit == 'tbs' or unit == 'tb' or unit == 'tbsp.' or unit == 'tbsps':
        unit = 'tbsp'
    elif unit == 'teaspoon' or unit == 'teaspoons' or unit == 'tsp.' or unit == 'tsps':
        unit = 'tsp'
    elif unit == 'c' or unit == 'cups':
        unit = 'cup'
    elif unit == 'grams' or unit == 'gram':
        unit = 'g'
    elif unit == 'milliliters' or unit == 'millilitres' or unit == 'mls':
        unit = 'ml'
    elif unit == 'pt' or unit == 'pints':
        unit = 'pint'
    elif unit == 'l' or unit == 'liter' or unit == 'litres' or unit == 'litres':
        unit = 'litre '
    elif unit == 'dashes':
        unit = 'dash'
    elif unit == 'ounce' or unit == 'ounces':
        unit = 'oz'
    elif unit == 'gram' or unit == 'grams':
        unit = 'g'
    elif unit == 'mgs':
        unit = 'mg'
    elif unit == 'gallon' or unit == 'gallons' or unit == 'gal':
        unit = 'gals'
    elif unit == 'gills' or unit == 'gill':
        unit = 'gill'
    elif unit == 'fl. oz':
        unit = 'fl.oz'
    elif unit == 'lbs' or unit == 'pound' or unit == 'pounds':
        unit = 'lb'
    elif unit == 'qt' or unit == 'quart.':
        unit == 'quart'
    elif unit == "mm's" or unit == 'mms' or unit == 'millimetres' or unit == 'millimeters':
        unit == 'mm'
    elif unit == 'centimetres' or unit == 'centimeters' or unit == 'cms' or unit == "cm's":
        unit == 'cm'
    elif unit == 'packets' or unit == 'pack' or unit == 'package' or unit == 'packages' or unit == 'box' or unit == 'packet' or unit == 'pkg':
        unit == 'pack'
    elif unit == 'slices':
        unit == 'slice'
    elif unit == 'handfuls':
        unit == 'handful'
    elif unit == 'dollops':
        unit == 'dollop'
    elif unit == 'tins':
        unit == 'tin'
    elif unit == 'pots':
        unit == 'pot'
    elif unit == 'cans':
        unit == 'can'
    elif unit == 'jars':
        unit == 'jar'
    elif unit == 'tins':
        unit == 'tin'
    elif unit == 'cartons':
        unit == 'carton'
    elif unit == 'heapings':
        unit == 'heaping'
    elif unit == 'dashes':
        unit == 'dash'
    elif unit == 'inches':
        unit == 'inch'
    elif unit == 'pinches':
        unit == 'pinch'
    elif unit == 'sprigs':
        unit == 'sprig'
    elif unit == 'packets':
        unit == 'packet'
    elif unit == 'bulbs' or 'head':
        unit == 'bulb'
    elif unit == 'cans':
        unit == 'can'
    elif unit == ' kg' or unit == 'kg ':
        unit == 'kg'

    return unit


def remove_fractions(remaining_string):
    unicode = ['½', '¼', '¾', '⅓', '⅛']
    for u in unicode:
        if u in remaining_string:
            remaining_string.replace(u, ' ')

    return remaining_string


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()




def strip_punctuation(remaining_string):
    for x in remaining_string:
        if x in string.punctuation:
            remaining_string = remaining_string.translate(
                str.maketrans('', '', string.punctuation))

    return remaining_string



def convert_units_to_grams(amount, unit, grams_per_cup, ingredient):

    # Search through the categories to see if we can assign the ingredient to one with the ingredient check variable
    gram_weight = False

    try:
        if unit == 'cup':
            serving_in_cups = amount
            gram_weight = serving_in_cups * grams_per_cup

        # Tablespoon
        elif unit == 'tbsp' or unit == 'heaping' or unit == 'dollop' or unit == 'scoop' or unit == 'handful':
            serving_in_cups = amount * 0.0625
            gram_weight = serving_in_cups * grams_per_cup

        # Teaspoon
        elif unit == 'tsp' or unit == 'sprig' or unit == 'sprinkle':
            serving_in_cups = amount * 0.0208333
            gram_weight = serving_in_cups * grams_per_cup

        # Other small volumes we are classing as 0.5 tsp
        elif unit == 'drop' or unit == 'pinch':
            serving_in_cups = amount * 0.0208333
            serving_in_cups = serving_in_cups / 2
            gram_weight = serving_in_cups * grams_per_cup

        # Fluid ounces
        elif unit == 'floz':
            serving_in_cups = amount * 0.125
            gram_weight = serving_in_cups * grams_per_cup

        # Dashes
        elif unit == 'dash':
            serving_in_cups = amount * 0.0026
            gram_weight = serving_in_cups * grams_per_cup

        # Millilitres
        elif unit == 'ml':
            serving_in_cups = amount * 0.00422675
            gram_weight = serving_in_cups * grams_per_cup

        # Litre
        elif unit == 'litre':
            serving_in_cups = amount * 4.22675
            gram_weight = serving_in_cups * grams_per_cup

        # Pint
        elif unit == 'pint':
            serving_in_cups = amount * 2.4019
            gram_weight = serving_in_cups * grams_per_cup

        # Gals
        elif unit == 'gals':
            serving_in_cups = amount * 19.2152
            gram_weight = serving_in_cups * grams_per_cup

        # Gills
        elif unit == 'gill':
            serving_in_cups = amount * 0.5
            gram_weight = serving_in_cups * grams_per_cup

        # Quart
        elif unit == 'quart':
            serving_in_cups = amount * 4
            gram_weight = serving_in_cups * grams_per_cup

        # DL
        elif unit == 'dl':
            serving_in_cups = amount * 0.422675
            gram_weight = serving_in_cups * grams_per_cup

        # GL
        elif unit == 'gl':
            serving_in_cups = amount * 19.2152
            gram_weight = serving_in_cups * grams_per_cup

        # Weight
        # MG
        elif unit == 'mg':
            gram_weight = amount / 1000

        # Ounce
        elif unit == 'oz':
            gram_weight = amount * 28.3495

        # Pound
        elif unit == 'lb':
            gram_weight = amount * 453.592

        # KG
        elif unit == 'kg':
            gram_weight = amount * 1000

        # Calculating the weight of ginger based on the cm
        # cm
        elif unit == 'cm':
            gram_weight = amount * 8

        # inch
        elif unit == 'inch':
            gram_weight = amount * 24

        # Grams
        elif unit == 'g' or unit == 'grams':
            gram_weight = amount

        #Can and Tins
        elif unit == 'can' or unit == 'tin' or 'unit' == 'cans':
            one_unit = float(400)
            gram_weight = one_unit * amount

        #Wedge (Lime)
        elif unit == 'wedge' and ingredient == 'lime':
            one_unit = 15
            gram_weight = one_unit * amount

        #Bulb (Garlic)
        elif unit == 'bulb' and ingredient == 'garlic':
            one_unit = 30
            gram_weight = one_unit * amount

        #Clove (Garlic)
        elif unit == 'clove' or unit == 'cloves':
            one_unit = 5
            gram_weight = one_unit * amount

        # Pack
        elif unit == 'pack':
            one_unit = 300
            gram_weight = one_unit * amount

        # Jar
        elif unit == 'jar':
            one_unit = 107
            gram_weight = one_unit * amount

        # Carton
        elif unit == 'carton':
            one_unit = 1000
            gram_weight = one_unit * amount

        # Pot
        elif unit == 'pot':
            one_unit = 500
            gram_weight = one_unit * amount

        # Slices
        elif unit == 'slice' or unit == 'slices':
            one_unit = 25
            gram_weight = one_unit * amount
            print(f'Gram weight {gram_weight}')

        elif unit == 'leaf' or unit == 'leaves':
            one_unit = 1.25
            gram_weight = one_unit * amount

        # Garnish
        elif unit == 'garnish' and 'nut' in ingredient or 'cashew' in ingredient:
            serving_in_cups = amount * 0.0625
            gram_weight = serving_in_cups * grams_per_cup

        else:
            gram_weight = None
            print('Cannot find gram weight for this ingredient')

        return gram_weight

    except Exception as e:
        pass


# ------------------ Generating the nutrient reliant data -------------------

# Get the predicted servings first if we dont have any
def servings_predicted(calories):
    servings_predicted = round(calories / 500)
    if servings_predicted == 0:
        servings_predicted = 1

    return servings_predicted


# Calculate calories from macros
def calculate_calories(nutrition):
    protein = nutrition['PROCNT']['quantity']
    carbs = nutrition['CHOCDF']['quantity']
    fat = nutrition['FAT']['quantity']
    calories = (protein * 4) + (carbs * 4) + (fat * 9)
    return calories


# Calculate the nutrition score based on the nutrition
def calculate_nutrition_score(servings, nutrition, firestore_nutrition):
    ''' Calculate the nutrition score based on the percentage of daily intake satisfied per nutrient '''
    nutrient_scores = []
    overall_nutrients_satisfied = []

    try:
        protein = nutrition['PROCNT']['quantity']
        fat = nutrition['FAT']['quantity']
        carbs = nutrition['CHOCDF']['quantity']
        has_all_macros = True
    except:
        has_all_macros = False

    # If has_all_macros is false then the nutrition will be an empty array
    if has_all_macros == True:

        # Calculating the Calories based on Macros
        calories = (protein * 4) + (carbs * 4) + (fat * 9)

        # Calculate predicted servings if none given
        if servings == None or servings == 0:
            servings = servings_predicted(calories)
        else:
            None

        # Consider the relative size of the meal to the daily calories
        calories_per_serving = calories / servings
        # 2250 is the average recommended daily calorie intake for adults
        ratio_of_daily_total = 2250 / calories_per_serving

        # Iterate through the firestore nutrients collection
        for key, value in nutrition.items():

            code = key
            quantity = value['quantity']
            quantity_per_serving = float(quantity/servings)

            # Stop sodium from looping round following for loop
            sodium_count = 0

            # Find the recommended amount for each nutrient
            for rec_nutrient in firestore_nutrition:

                # Match it to the nutrients in the nutrient file
                # Protein and Fibre are not micros
                # Carbs and fats arent in the firestore nutrition collection
                if rec_nutrient['code'] == code and code != 'PROCNT' and code != 'FIBTG':

                    # Get the code and the recommended quantity
                    rec_quantity = rec_nutrient['lower_rec']

                    # Get the calorie adjusted percentage
                    percentage_satisfied = float(
                        quantity_per_serving / rec_quantity)

                    # Individual nutrient score is the score for each nutrient
                    individual_nutrient_score = ratio_of_daily_total * percentage_satisfied

                    # If the score is greater than 1 we will stop it (at 100%)
                    if individual_nutrient_score > 1:
                        individual_nutrient_score = 1

                    # Append to list to compute the nutrient score
                    overall_nutrients_satisfied.append(
                        individual_nutrient_score)

                # If the nutrient is sodium (not in the nutrients file at the moment)
                elif code == 'NA' and sodium_count < 1:
                    rec_quantity = 2300

                    # Get the calorie adjusted percentage
                    percentage_satisfied = float(
                        quantity_per_serving / rec_quantity)
                    individual_nutrient_score = ratio_of_daily_total * percentage_satisfied
                    sodium_count = sodium_count+1

                    # When sodium is over the recommended it start to subtract the more it increases
                    # Too much salt is not good
                    if individual_nutrient_score > 1:
                        subtract = float(individual_nutrient_score - 1)
                        individual_nutrient_score = 1 - subtract

                        # If its goes less than 0 - keep it at 0
                        if individual_nutrient_score < 0:
                            individual_nutrient_score = 0

                    # Append sodium to the list
                    overall_nutrients_satisfied.append(
                        individual_nutrient_score)

        # Get the average percentage from the list of individual scores
        nutrient_percentage = mean(overall_nutrients_satisfied)
        # print('Nutrient percentage :', nutrient_percentage)

        # Convert score to out of 10 and round to 2dp
        nutrient_score = nutrient_percentage * 10
        nutrient_score = round(nutrient_score, 2)

        # Add all nutrient score to a list to plot
        nutrient_scores.append(nutrient_score)

        # Update Firestore
        nutrition_score_update = {}
        nutrition_score_update['micronutrient_score'] = nutrient_score

        return nutrition_score_update

 

def add_nutrition_per_serving(nutrition, servings):
    ''' Calculate the nutrition per serving '''
    nutrition_per_serving = {}
    for nutrient_code, nutrient_dict in nutrition.items():
        nutrient = {}
        quantity_adjusted = nutrient_dict['quantity'] / servings

        nutrient.update(
            {'label': nutrient_dict['label'], 'quantity': quantity_adjusted, 'unit': nutrient_dict['unit']})
        nutrition_per_serving.update({nutrient_code: nutrient})

    nutrition_per_serving_update = {
        'nutrition_per_serving': nutrition_per_serving}

    nutrition_per_serving_update.update(protein_per_serving_grams = nutrition_per_serving["PROCNT"]["quantity"])
    nutrition_per_serving_update.update(carbs_per_serving_grams = nutrition_per_serving["CHOCDF"]["quantity"])
    nutrition_per_serving_update.update(fat_per_serving_grams = nutrition_per_serving["FAT"]["quantity"])

    return nutrition_per_serving_update



def search_for_alternatives_gluten_and_states(raw_ingredients, ingredients_formatted, ingredient_list):
    ''' Search for alternative ingredients in the raw_ingredients '''
    # 1. Find alternatives ingredients which arent split
    # Search the core ingredients a match in the raw ingredient
    for index, raw_ingredient in enumerate(raw_ingredients):
        found_ingredient = False

        # Store 'None' formatted unit as '0' else null it will cause error below
        formatted_unit = ingredients_formatted[index]['unit']
        if formatted_unit == None:
            formatted_unit = '0'

        for ingredient_search in ingredient_list:
            if found_ingredient == False:
                try:
                    # If the ingredient is found inside the raw ingredient
                    # and is not the one already found or a smaller word inside it
                    # and is less than 80% similar to the current one (we dont want different spellings)
                    # and is less than 80% similar to the current unit - e.g. garlic x cloves
                    if ingredient_search in raw_ingredient \
                            and ingredient_search not in ingredients_formatted[index]['ingredient'] \
                            and similar(ingredient_search, ingredients_formatted[index]['ingredient']) < 0.8\
                            and similar(ingredient_search, formatted_unit) < 0.8\
                            and found_ingredient == False:
                        # If there are already alternatives provided, append to list
                        try:
                            ingredients_formatted[index]['alternative_provided'].append(
                                ingredient_search)
                        # If there are no alternatives provided, create the list with the first ingredient
                        except:
                            ingredients_formatted[index].update(
                                {'alternative_provided': ingredient_search})

                        found_ingredient = True

                    else:
                        None

                except:
                    print('Error finding alternative ingredient')

    # Iterate through the raw ingredients again
    # Get more alternatives and keywords which could have useful info
    for index, raw_ingredient in enumerate(raw_ingredients):

        # Gluten free
        for word in ['gluten free', 'gluten-free', 'gf', 'glutenfree']:
            if word in raw_ingredient:
                ingredients_formatted[index].update({'gluten_free': True})

        # Cooking states
        for state in ['uncooked', ' cooked']:
            if word in raw_ingredient:
                ingredients_formatted[index].update({'state': state})

        # 2. Get alternatives when they are split by an or/comma. E.g. almond or oat milk
        # Split the string on the ingredient already found
        if ' or ' in raw_ingredient or ',' in raw_ingredient:
            raw_ingredient.replace(',', ' or ')
            raw_ingredient_split = raw_ingredient.split(' or ')
            current_ingredient_split = ingredients_formatted[index]['ingredient'].split(
            )

            for sub_string in raw_ingredient_split:
                # We only want to match one ingredient from each split - if there is one itll be the longest string
                found_ingredient_from_split = False
                # Combine the last word in the string with the substring and search for a match
                # This should work in cases like almond or oat milk
                ingredient_to_search = sub_string + \
                    ' ' + current_ingredient_split[-1]
                for ingredient_search in ingredient_list:
                    # If theres a match and we havent already found one from this split
                    if ingredient_to_search == ingredient_search and found_ingredient_from_split == False:
                        ingredients_formatted[index].update(
                            {'alternative_provided': ingredient_to_search})
                        found_ingredient_from_split = True

    ingredients_formatted_update = {
        'ingredients_formatted': ingredients_formatted}

    return ingredients_formatted_update


def add_alternatives_to_map(ingredients_formatted, ingredients_map, ingredients_collection):

    for ingredient_data in ingredients_formatted:

        ingredient = ingredient_data['ingredient']
        for ingredient_dict in ingredients_collection:
            if ingredient == ingredient_dict['ingredient'] and ingredient_dict['alternatives'] != None:
                for ingredient in ingredient_dict['alternatives']:
                    underscore_ingredient = ingredient.replace(
                        ' ', '_')
                    map_update = {underscore_ingredient: True}
                    ingredients_map.update(map_update)

    map_update = {'ingredients_map': ingredients_map}

    return map_update



# ----------------- Calculate the nutrition ----------------

# Runs the script
def run_nlp(ingredient_input, servings):
    ''' This is the main function that runs the calculator '''
    ingredient_input = ingredient_input.split(",")
    servings = int(servings)

    # Pull ingredients list from firestore
    ingredients_collection = get_ingredients_collection()
    firestore_nutrition = get_recommended_nutrition()
    ingredient_list = ingredient_search()

    ingredients_formatted = []

    # Iterate through each ingredient in the list
    for raw_string in ingredient_input:

        try:
            # Clean ingredient pre looking for a match
            raw_string = ingredient_pre_cleanse(raw_string)

            # Remove accents and symbols
            raw_string = remove_accents_and_symbols(raw_string)

            ingredient_found = False
            # Iterate and find the true matches to the display ingredient first
            for ingredient_pair in ingredient_list:
                if ingredient_pair['raw_ingredient'] in raw_string and ingredient_found == False:
                    if ingredient_pair['raw_ingredient'] == ingredient_pair['display_ingredient']:
                        ingredient = ingredient_pair['display_ingredient']
                        ingredient_found = True
                        break

            if ingredient_found:

                # Create dict to store the result
                final_ingredient = ingredient.strip()

                # Get the quantity from the function
                quantity = get_quantity(raw_string)
 
                # Strip the punctuation
                remaining_string = raw_string.replace('/', ' ')
                remaining_string = strip_punctuation(remaining_string)

                # Now remove the rest of the digits with regex
                remaining_string = re.sub(r'\d+', '', remaining_string)
                remaining_string = remove_fractions(remaining_string)

                # Get units
                measurement_unit = get_unit(remaining_string)
                unit = convert_units(measurement_unit)

                # Remove units from remaining string
                remaining_string = remove_units(remaining_string)

                structured_ingredient = {}
                structured_ingredient['ingredient'] = final_ingredient
                structured_ingredient['quantity'] = quantity
                structured_ingredient['unit'] = unit

                # Append to the list of ingredients for the recipe
                ingredients_formatted.append(structured_ingredient)

        except Exception as e:
            pass

    # Now we've strucured the raw data, create an object to load the calculated fields into
    recipe_object = {
        'ingredients_formatted': ingredients_formatted, 'servings': servings}

    # Calculate nutrition
    nutrition_object = calculate_nutrition(
        ingredients_formatted, servings, ingredients_collection)
    nutrition = nutrition_object['nutrients']

    # Calculate calories
    calories = calculate_calories(nutrition)

    # Repredict the servings with the new calories and update firestore
    if servings == False:
        servings = servings_predicted(calories)
        print('Servings have been predicted')

    # Update nutrition score
    nutrition_score_update = calculate_nutrition_score(
        servings, nutrition, firestore_nutrition)
    recipe_object.update(nutrition_score_update) 

    # Update nutrition per serving
    nutrition_per_serving_update = add_nutrition_per_serving(
        nutrition, servings)
    nutrition_per_serving_update.update({"calories_per_serving" : nutrition_object["calories_per_serving"]})
    recipe_object.update(nutrition_per_serving_update)

    # Add alternatives to search
    # Ingredients map will be empty as its a new recipe
    ingredients_map = {}
    ingredient_map_update = add_alternatives_to_map(
        ingredients_formatted, ingredients_map, ingredients_collection)
    recipe_object.update(ingredient_map_update)

    return recipe_object


def calculate_nutrition(ingredients, servings, ingredients_collection):

    # Nutrient codes and their display names
    nutrient_names = {'PROCNT': 'Protein',
                      'CHOCDF': 'Total Carbs',
                      'FAPU': 'Polyunsaturated Fat',
                      'FAMS': 'Monounsaturated Fat',
                      'FASAT': 'Saturated Fat',
                      'FAT': 'Total Fat',
                      'SUGAR': 'Total Sugars',
                      'CA': 'Calcium',
                      'FIBTG': 'Fiber',
                      'NA': 'Sodium',
                      'VITA_RAE': 'Vitamin A',
                      'THIA': 'Vitamin B1',
                      'RIBF': 'Vitamin B2',
                      'NIA': 'Vitamin B3',
                      'VITB6A': 'Vitamin B6',
                      'FOLDFE': 'Vitamin B9',
                      'VITB12': 'Vitamin B12',
                      'VITC': 'Vitamin C',
                      'VITD': 'Vitamin D',
                      'TOCPHA': 'Vitamin E',
                      'VITK1': 'Vitamin K',
                      'ZN': 'Zinc',
                      'CU': 'Copper',
                      'FE': 'Iron',
                      'MG': 'Magnesium',
                      'P': 'Phosphorus',
                      'K': 'Potassium',
                      'MN': 'Manganese',
                      'SE': 'Selenium',
                      'ASH': 'Ash'}

    recipe_nutrition = []

    # Iterate through the ingredients
    for ingredient_dict in ingredients:

        # Get the ingredient name
        recipe_ingredient = ingredient_dict['ingredient']
        recipe_ingredient = recipe_ingredient.replace('-', ' ')
        unit = ingredient_dict['unit']
        quantity = ingredient_dict['quantity']
        if quantity == None:
            quantity = float(1)

        contains_nutrition = False
        found_ingredient = False
        for ingredient_dict in ingredients_collection:
            if recipe_ingredient == ingredient_dict['ingredient']:
                ingredient = ingredient_dict['ingredient']
                found_ingredient = True

                # Get usda data
                try:
                    usda_data = ingredient_dict['usda_data']
                except:
                    usda_data = None

                # Check for nutrition
                try:
                    has_nutrition = usda_data['usda_nutrition']
                    contains_nutrition = True
                except:
                    contains_nutrition = False

                # Get grams per cup
                try:
                    grams_per_cup = usda_data['grams_per_cup']
                except:
                    grams_per_cup = None

                # Get grams per quantity
                try:
                    grams_per_quantity = usda_data['grams_per_quantity']
                except:
                    grams_per_quantity = None

                try:
                    average_serving_grams = usda_data['average_serving_grams']
                except:
                    average_serving_grams = False

        # If we havent found the ingredient in the display ingredient - search the alternatives
        if found_ingredient == False:

            for ingredient_dict in ingredients_collection:
                if ingredient_dict['alternatives'] != None:
                    if recipe_ingredient in ingredient_dict['alternatives']:
                        ingredient = ingredient_dict['ingredient']
                        found_ingredient = True

                        # Get usda data
                        try:
                            usda_data = ingredient_dict['usda_data']
                        except:
                            usda_data = None

                        # Check for nutrition
                        try:
                            has_nutrition = usda_data['usda_nutrition']
                            contains_nutrition = True
                        except:
                            contains_nutrition = False

                        # Get grams per cup
                        try:
                            grams_per_cup = usda_data['grams_per_cup']
                        except:
                            grams_per_cup = None

                        # Get grams per quantity
                        try:
                            grams_per_quantity = usda_data['grams_per_quantity']
                        except:
                            grams_per_quantity = None

                        try:
                            average_serving_grams = usda_data['average_serving_grams']

                        except:
                            average_serving_grams = False

        # ------------- Convert the ingredient into the required units ------------

        if contains_nutrition == True:

            weight_found = False

            # If there is a unit then we will calculate the amount in grams by converting the units
            if unit != None:
                gram_weight = convert_units_to_grams(
                    quantity, unit, grams_per_cup, ingredient)

                if gram_weight != None:
                    weight_found = True
                else:
                    weight_found = False

                # If we cant calculate weight from the unit (some can be too vague) try the average serving weight
                if weight_found == False and grams_per_quantity:
                    try:
                        gram_weight = grams_per_quantity * quantity
                        weight_found = True

                    except Exception as e:
                        print('Error multiplying gram by quantity')

            # If there are no units then use the grams per quantity
            elif grams_per_quantity:
                try:
                    grams_per_quantity = float(grams_per_quantity)
                    gram_weight = grams_per_quantity * quantity
                    weight_found = True

                except Exception as e:
                    print('Error at the grams per quantity stage')

            # If there are no grams per quantity, there should be an average serving
            if weight_found == False and average_serving_grams:
                try:
                    gram_weight = average_serving_grams
                    weight_found = True

                except Exception as e:
                    print(
                        'Error at the average serving stage. We cant get the nutrition for this ingredient yet')

            # If we have found a weight for the ingredient, find the nutrition
            if weight_found == True:
                try:

                    # Get the nutrition list from the ingredient data
                    nutrition_list = usda_data['usda_nutrition']

                    # Iterate through the list and get each nutrient
                    for nutrient_dict in nutrition_list:
                        for nutrient_name, nutrient_value in nutrient_dict.items():

                            # Get the quantity per 100g
                            # Convert it to a float if it isnt already
                            per_100g = nutrient_value['quantity']
                            if isinstance(per_100g, str):
                                per_100g = per_100g.replace(',', '')
                                per_100g = float(per_100g)
                            nutrient_unit = nutrient_value['unit']

                            # Make sure the units are standardised
                            if nutrient_unit == 'mcg':
                                nutrient_unit = 'µg'

                            # Next we need to standardise the units and quantities to grams
                            # This means we can calculate the total nutrition, because nutrient values can be in g, mg, mcg
                            if per_100g != 0:
                                if nutrient_unit == 'g':
                                    per_100g = per_100g
                                elif nutrient_unit == 'mg':
                                    per_100g = per_100g/1000
                                    # print('Mg converted')
                                elif nutrient_unit == 'µg':
                                    per_100g = per_100g / 1000000
                                    # print('Mcg converted')

                            # Divide the gram weight of the ingredient by 100 to get the relative weight to the nutrient
                            required_amount = 100 / float(gram_weight)

                            # Divide the value per 100g by the required amount to get the nutrient amount in grams
                            nutrient_amount = per_100g / required_amount

                            # print(nutrient_name, ': ', nutrient_amount, ' ', nutrient_unit)
                            nutrition_data = {
                                'nutrient': nutrient_name, 'amount': nutrient_amount, 'unit': nutrient_unit}
                            # print(nutrition_data)

                            # Append the nutrient amount to the list for the ingredient
                            # The current nurient amount for each ingredient will be added to the new nutrient amount
                            total_appended = False
                            if len(nutrition_data) > 0:
                                for index, nutrient in enumerate(recipe_nutrition):
                                    # Find the matching nutrient code
                                    if nutrition_data['nutrient'] == nutrient['nutrient']:

                                        # Total the amounts
                                        updated_amount = float(
                                            nutrition_data['amount'] + nutrient['amount'])
    
                                        # Create dictionary to update the running total
                                        update = {
                                            'nutrient': nutrient_name, 'amount': updated_amount, 'unit': nutrient_unit}
                    
                                        # Update the nutrition at the current index
                                        recipe_nutrition[index] = update
                                        total_appended = True

                            if total_appended == False:
                                recipe_nutrition.append(nutrition_data)

                except Exception as e:
                    print('No nutrition for this ingredient')

        else:
            print('')
            print('No nutrition for this ingredient yet')
            print('')

    # Create a dictionary to store the data for each nutrient per recipe
    final_recipe_nutrition = {}


    # Iterate through the nutrients to get the final recipe nutrition
    for y in recipe_nutrition:
        nutrient = y['nutrient']
        quantity = y['amount']
        unit = y['unit']

        # Re-convert quantities depending on the unit
        if unit == 'mg':
            quantity = quantity * 1000
        if unit == 'mcg' or unit == 'µg':
            quantity = quantity * 1000000

        # Get the nutrient display name from the top object
        for nutrient_code in nutrient_names:
            if nutrient == nutrient_code:
                display_name = nutrient_names.get(nutrient)

        # Finally, create an object for the nutrient
        final_nutrient = {nutrient: {'quantity': quantity,
                                     'unit': unit, 'label': display_name}}
        # And append it to the final list
        final_recipe_nutrition.update(final_nutrient)

    # Get the RDV
    nutrients_required = get_nutrients_from_firestore()

    nutrient_names = []
    quantities = []
    percentages_of_rdv = []

    # Calculate the total calories per serving
    protein_quantity = final_recipe_nutrition['PROCNT']['quantity']
    fat_quantity = final_recipe_nutrition['FAT']['quantity']
    carbs_quantity = final_recipe_nutrition['CHOCDF']['quantity']
    total_calories = (protein_quantity * 4) + \
        (carbs_quantity * 4) + (fat_quantity * 9)
    calories_per_serving = total_calories / servings
    calories_per_serving = round(calories_per_serving, 2)

    for nutrient, data in final_recipe_nutrition.items():
        # Get the quantity and divide it by the number of servings entered
        quantity = data['quantity']
        quantity = quantity / servings
        # Get the label and unit and combine for the table headers
        label = data['label']
        unit = data['unit']
        nutrient_name = label + ' (' + unit + ')'
        # print(nutrient_name)

        get_nutrient = False

        if nutrient == 'CHOCDF':
            rec_quantity = float(300)
            get_nutrient = True
        if nutrient == 'PROCNT':
            rec_quantity = float(75)
            get_nutrient = True
        if nutrient == 'FAT':
            rec_quantity = float(66)
            get_nutrient = True

        else:
            for rec_nutrient in nutrients_required:
                if rec_nutrient['code'] == nutrient:

                    # Get the recommended quantity
                    rec_quantity = rec_nutrient['lower_rec']
                    get_nutrient = True

        if get_nutrient == True:
            # Get the calorie adjusted percentage
            percentage_satisfied = float(quantity / rec_quantity)
            percentage_satisfied = percentage_satisfied * 100
            # Limit the percentage satisfied to 100
            if percentage_satisfied > 100:
                percentage_satisfied = 100
            percentages_of_rdv.append(percentage_satisfied)
            nutrient_names.append(nutrient_name)
            quantities.append(quantity)


    # Add list to firetore recipe - the new nutrients will overwrite the current edamam nutrition
    nutrition_update = {'nutrients': final_recipe_nutrition, "calories_per_serving" : calories_per_serving}
    
    return nutrition_update



