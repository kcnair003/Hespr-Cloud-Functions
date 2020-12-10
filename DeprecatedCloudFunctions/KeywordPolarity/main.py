from firebase import firebase
import firebase_admin
from firebase_admin import db, credentials
import json

firebase = firebase.FirebaseApplication('https://hesprmvp.firebaseio.com', None)
default_app = firebase_admin.initialize_app(options={'databaseURL': 'https://hesprmvp.firebaseio.com'})

# Defines a function to find the weighted average of a set of polarities
def find_weighted_average(selected, total, num):
     weighted_avg = (((num - 2)/(num * num)) * selected) + (((num - 1)/(num * num)) * total)
     return(weighted_avg)

# Defines a function that calculates and normalizes all of the image polarities
def find_final_polarity(keyword):
     # Defines the total polarity as 0, which is then increased by the image polarities
     total_polarity = 0
     # References the realtime database
     total_ref = db.reference(f'/keyword_polarity/{keyword}/images/')
     # Defines lists and a dictionary for the data in the realtime database
     total_ref_dict = total_ref.get()
     total_ref_keys = list(total_ref_dict.keys())
     total_ref_values = list(total_ref_dict.values())
     # Declares a dictionary that will be used to define the output
     output_dict = {}
     # Finds the total polarity
     for value in total_ref_values:
          total_polarity += value
     # Defines the number of images
     num_images = len(total_ref_keys)
     # Defines a for loop that will calculate and normalize the image polarities
     for key in total_ref_keys:
          selected_polarity = total_ref_dict[key]
          final_keyword_polarity = find_weighted_average(selected_polarity, total_polarity, num_images)
          image_num = total_ref_keys.index(key) + 1
          keyword_polarity_ref = f'/keyword_polarity/{keyword}/selectedImagePolarity/'
          child_node_name = 'selected_image' + f'{str(image_num)}' + '_polarity'
          firebase.put(keyword_polarity_ref, child_node_name, final_keyword_polarity)
          output_dict[key] = final_keyword_polarity
     # Prints the dictionary that represents the output 
     print(output_dict)

def keyword_polarity(event, context):
    """Triggered by a change to a Firebase RTDB reference.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    resource_string = context.resource
    # print out the resource string that triggered the function
    print(f"Function triggered by change to: {resource_string}.")
    # now print out the entire event object
    print(str(event))
    # Finds the name of the keyword
    resource_string_list = resource_string.split('/')
    keyword_name = resource_string_list[6]
    find_final_polarity(keyword_name)