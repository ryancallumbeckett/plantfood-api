#Functions for recipe conversions


def convert_units_to_grams(amount, unit, grams_per_cup, ingredient):

    # Search through the categories to see if we can assign the ingredient to one with the ingredient check variable
    gram_weight = False

    try:
        if 'cup' in unit:
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

        # Garnish
        elif unit == 'garnish' and 'nut' in ingredient or 'cashew' in ingredient:
            # Convert into cups
            serving_in_cups = amount * 0.0625
            gram_weight = serving_in_cups * grams_per_cup

            # Find the gram weight from the weight per cup
            gram_weight = serving_in_cups * grams_per_cup

        else:
            gram_weight = None
            # print('Cannot find gram weight for this ingredient')

        return gram_weight

    except Exception as e:
        print('Error on unit conversion')
        print(e)

result = convert_units_to_grams(2, "cups", 250, "sugar")
print(result)