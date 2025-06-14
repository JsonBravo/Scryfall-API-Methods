#v1.0

#imports ----------------------------------------------------------------------------------
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
import time
import numpy as np
import ast
import tkinter as tk
from tkinter import messagebox

# scryfall API methods ---------------------------------------------------------------------------------- 
def bulk_oracle_scry():
    """
    Review Bulk Data availability here:
    https://scryfall.com/docs/api/bulk-data
    Review Bulk Data API here:
    https://scryfall.com/docs/api/bulk-data/all

    # This is the 'Oracle Cards' json data link of the day (containing one Scryfall card object for each Oracle ID on Scryfall) -- there are other bulk data options on scryfall...
    """
    response = requests.get("https://api.scryfall.com/bulk-data") #this is the url to the day's bulk json data links on Scryfall website
    data = response.json()
    time.sleep(0.5)
    response = requests.get(data['data'][0]['download_uri']) #this is the 'Oracle Cards' json data link of the day (containing one Scryfall card object for each unique play card on Scryfall)
    data = response.json()
    time.sleep(0.5)
    return data

# ------------------------------------------------------------------------------------------------------
def scry(q, unique = True):
    """
    Review query (q) syntax here:
    https://scryfall.com/docs/syntax
    example of final data structure needed within method:
    query={"q":"oracle:goad format:commander", "unique": "cards"}
    ...where the passed q = "oracle:goad format:commander" and passed unique = True or False
    # TESTING
    scry("oracle:goad name:Mutation format:commander") #should return a json like data structure with a single card object (Acquired Mutation)  
    """
    url = "https://api.scryfall.com/cards/search"
    #build up scry query
    query = {"q":q}
    if unique:
        query["unique"] = "cards"
        all_cards = []
        has_more = True
        page = 1
    while has_more:
        response = requests.get(url, params=query)
        data = response.json()
        # Add cards from the current page
        all_cards.extend(data.get('data', []))
        # Check if there's another page
        has_more = data.get("has_more", False)
        # Update the URL to the next page if more cards exist
        if has_more:
            print("---- New Page ----")
            query['page'] = page
            if page > 5:
                has_more = False
            else:
                page += 1
    time.sleep(0.5)
    return all_cards

# ------------------------------------------------------------------------------------------------------
def scry_all():
    print("Manually download the full dataset online from https://scryfall.com/docs/api/bulk-data ('All Cards' includes re-prints)... Method for pulling this within script is not available at this time.")

# scryframe building methods -------------------------------------------------------------------------------------
"""
Requirements:
import pandas as pd
import numpy as np
"""
def standard_price(prices):
    #prices=return_as_dict(prices)
    primary_price_key = 'usd'
    alternative_key = 'usd_foil'
    standard_price = 0.00 #usd // default
    if (primary_price_key in prices) and (prices[primary_price_key] != None):
        standard_price = prices[primary_price_key]
    elif (alternative_key in prices) and (prices[alternative_key] != None):
        standard_price = prices[alternative_key]
    else:
        temp = 0.00 # used to determine the avg price if any
        count = 0
        for key in prices:
            if prices[key] != None:
                value = prices[key]
                if str(value).replace('.', '', 1).isdigit():
                    value = float(value)
                    temp = temp + value
                    count = count + 1
        if temp > 0.00:
            standard_price = temp/count
    return standard_price

# ------------------------------------------------------------------------------------------------------
def expand_prices(prices):
    data = {}
    for price_type in prices:
        data_key = ('price_'+price_type)
        if prices[price_type] != None:
            data[data_key] = float(prices[price_type])
        else:
            data[data_key] = None
    return data

# ------------------------------------------------------------------------------------------------------
def frame_the_scry(raw_scry):
    #Identify the data getting put into columns, needs to match respective keys in raw scry
    col_names = ['id','name','layout', 'mana_cost', 'cmc', 'type_line', 'oracle_text', 'power', 'toughness', 'colors', 'color_identity', 'keywords', 'rarity', 'artist','artist_ids','legalities', 'games', 'reserved', 'flavor_text', 'set_name', 'set_type', 'prices','image_uris']
    #initialize card data
    card_data = {key:[] for key in col_names}
    #loop through card data and pull items into frame
    for card in raw_scry:
        #print(f"Loading {card['name']}") #testing...
        #load card data
        [card_data[key].append(card[key]) if key in card.keys() else card_data[key].append(np.nan) for key in col_names]
        #check for extra card faces
        if "card_faces" in card.keys():
            for card_face in card['card_faces']:
                #print(f"--- Loading Card Face {card_face['name']}")
                #load card face data
                [card_data[key].append(card_face[key]) for key in col_names if key in card_face.keys()]
                #with the new card face row data, fill in data gaps with previous info
                max_count = max([len(card_data[key]) for key in col_names])
                [card_data[key].append(card_data[key][-1]) for key in col_names if len(card_data[key]) < max_count]
    #set the df with the card data
    df = pd.DataFrame(card_data)
    return df

# ------------------------------------------------------------------------------------------------------
def minimize_scryframe(df, select_columns = ['id','name','image_uris', 'layout', 'mana_cost','cmc', 'rarity','type_line', 'oracle_text', 'power', 'toughness', 'colors', 'color_identity', 'keywords', 'price']): # ---------------------------------------------------------------------------
    #Assumes the df came from the 'frame_the_scry' method
    if 'price' in select_columns:
        #price reporting
        df['price'] = [standard_price(x) for x in df['prices']]
        df['price'] = pd.to_numeric(df['price'])
    #At this time, I am leaving the following commented out...
    # ... making the id column a categorical will increase the memory space needed to maintain the final df.    
    #if 'id' in select_columns:
    #    df['id'] = df['id'].astype("category")
    return df[select_columns]

# ------------------------------------------------------------------------------------------------------

# scryframe printing methods ----------------------------------------------------------------------------
""" Requirements
from PIL import Image
from io import BytesIO
import time
import ast
"""
# ------------------------------------------------------------------------------------------------------
def show_image(image_url):
    try:
        # Download and display the image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        #img.show() # Opens the image in the default image viewer (good for Pythonista... not so much for computer...)
        display(img)
        time.sleep(0.5)
    except requests.exceptions.RequestException as e:
        print(f"No Image: {e}")

# ------------------------------------------------------------------------------------------------------
def pretty_print(df, show_images = True, image_size = ['small','normal','large'][0]):
    """If show_image is True, then the default size is 'small'... any of the three options can be passed, though... """
    if show_images == False:
        df = df.drop(columns=['image_uris'], errors='ignore')
    print("-------------------------------------")
    print(f"Card printing starting: {len(df)} Cards")
    print("(note: there is a 0.5 second delay printing in between cards if show_image = True)")
    for _, row in df.iterrows():
        print("-------------------------------------")
        #print(df['image_uris'])
        for col in df:
            if col != 'image_uris':
                print(f'|| {col}: {row[col]}')
            elif pd.isna(row[col]):
                print(f'|| {col}: {row[col]} [No Image]')
            else:
                if isinstance(row[col], dict):
                    show_image(row[col][image_size])# image_size can only be small, normal, or large
                else:
                    show_image(ast.literal_eval(row[col])[image_size])
    print("-------------------------------------")
    print(f"Card printing complete: {len(df)} Cards")
    print("-------------------------------------")
