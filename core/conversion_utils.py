
# Converts units into a standardised format
def convert_units_to_lemma(measurement_unit):
    unit = measurement_unit

    if unit == 'tablespoons' or unit == 'tablespoon' or unit == 'tbs' or unit == 'tb' or unit == 'tbsp.' or unit == 'tbsps':
        unit = 'tbsp'
    elif unit == 'teaspoon' or unit == 'teaspoons' or unit == 'tsp.' or unit == 'tsps':
        unit = 'tsp'
    elif unit == 'c' or unit == 'cups':
        unit = 'cup'
    elif unit == 'grams' or unit == 'gram' or unit == 'gms':
        unit = 'g'
    elif unit == 'milliliters' or unit == 'millilitres' or unit == 'mls':
        unit = 'ml'
    elif unit == 'pt' or unit == 'pints':
        unit = 'pint'
    elif unit == 'l' or unit == 'liter' or unit == 'litres' or unit == 'litres':
        unit = 'litre' 
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
    elif 'tin' in unit:
        unit == 'tin'
    elif unit == ' pots ' or unit == ' pot ':
        unit == 'pot'
    elif 'can' in unit:
        unit == 'can'
    elif 'jars' in unit:
        unit == 'jar'
    elif 'tins' in unit:
        unit == 'tin'
    elif unit == 'cartons':
        unit == 'carton'
    elif unit == 'heapings':
        unit == 'heaping'
    elif unit == 'dashes':
        unit == 'dash'
    elif 'inches' in unit:
        unit == 'inch'
    elif 'pinches' in unit:
        unit == 'pinch'
    elif unit == 'sprigs':
        unit == 'sprig'
    elif unit == 'packets':
        unit == 'packet'
    elif unit == 'bulbs' or 'head':
        unit == 'bulb'
    elif unit == ' kg' or unit == 'kg ':
        unit == 'kg'

    return unit


#First we need a function to convert all of the units into grams so we can get the nutrition from the usda data
def convert_units_to_grams(amount, unit, grams_per_cup, ingredient):

    # Search through the categories to see if we can assign the ingredient to one with the ingredient check variable
    gram_weight = False

    try:
        #Cup
        if unit == 'cup':
            #We already have the volume in the required unit
            serving_in_cups = amount
            gram_weight = serving_in_cups * grams_per_cup

        #Tablespoon
        elif unit == 'tbsp' or unit == 'heaping' or unit == 'dollop' or unit == 'scoop' or unit == 'handful':
            serving_in_cups = amount * 0.0625
            gram_weight = serving_in_cups * grams_per_cup

        #Teaspoon
        elif unit == 'tsp' or unit == 'sprig' or unit == 'sprinkle':
            serving_in_cups = amount * 0.0208333
            gram_weight = serving_in_cups * grams_per_cup

        #Other small volumes we are classing as 0.5 tsp
        elif unit == 'drop' or unit == 'pinch':
            serving_in_cups = amount * 0.0208333
            serving_in_cups = serving_in_cups / 2
            gram_weight = serving_in_cups * grams_per_cup

        #Fluid ounces
        elif unit == 'floz':
            serving_in_cups = amount * 0.125
            gram_weight = serving_in_cups * grams_per_cup

        #Dashes
        elif unit == 'dash':
            serving_in_cups = amount * 0.0026
            gram_weight = serving_in_cups * grams_per_cup

        #Millilitres
        elif unit == 'ml':
            serving_in_cups = amount * 0.00422675
            gram_weight = serving_in_cups * grams_per_cup  

        #Litre
        elif unit == 'litre':
            serving_in_cups = amount * 4.22675
            gram_weight = serving_in_cups * grams_per_cup

        #Pint
        elif unit == 'pint':
            serving_in_cups = amount * 2.4019
            gram_weight = serving_in_cups * grams_per_cup

        #Gals
        elif unit == 'gals':
            serving_in_cups = amount * 19.2152
            gram_weight = serving_in_cups * grams_per_cup

        #Gills
        elif unit == 'gill':
            serving_in_cups = amount * 0.5
            gram_weight = serving_in_cups * grams_per_cup

        #Quart
        elif unit == 'quart':
            serving_in_cups = amount * 4
            gram_weight = serving_in_cups * grams_per_cup

        #DL
        elif unit == 'dl':
            serving_in_cups = amount * 0.422675
            gram_weight = serving_in_cups * grams_per_cup

        #GL
        elif unit == 'gl':
            serving_in_cups = amount * 19.2152
            gram_weight = serving_in_cups * grams_per_cup

        #MG
        elif unit == 'mg':
            gram_weight = amount / 1000

        #Ounce
        elif unit == 'oz':
            gram_weight = amount * 28.3495

        #Pound
        elif unit == 'lb':
            gram_weight = amount * 453.592

        #KG
        elif unit == 'kg':
            gram_weight = amount * 1000

        #CM
        elif unit == 'cm':
            gram_weight = amount * 8

        #inch
        elif unit == 'inch':
            gram_weight = amount * 24

        #Grams
        elif unit == 'g' or unit == 'grams':
            gram_weight = amount

        #Can and Tins
        elif unit == 'can' or unit == 'tin' or unit == 'cans':
           one_unit = float(400)
           gram_weight = one_unit * amount

        #Slice (bread)
        elif unit == 'slice':
            one_unit = 38
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

        #Pack
        elif unit == 'pack':
            one_unit = 300
            gram_weight = one_unit * amount

        #Jar
        elif unit == 'jar':
            one_unit = 107
            gram_weight = one_unit * amount

        #Carton
        elif unit == 'carton':
            one_unit = 1000
            gram_weight = one_unit * amount

        #Pot
        elif unit == 'pot':
            one_unit = 500
            gram_weight = one_unit * amount

        #Garnish
        elif unit == 'garnish' and 'nut' in ingredient or 'cashew' in ingredient:
            serving_in_cups = amount * 0.0625
            gram_weight = serving_in_cups * grams_per_cup

        else:
            gram_weight = None
            print('Cannot find gram weight for this ingredient')

        return gram_weight

    except Exception as e:
        print('Error')
        print(e)


