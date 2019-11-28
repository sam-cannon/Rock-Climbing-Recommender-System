import sys
import os
import time
import numpy as np
import pandas as pd
import sklearn
import matplotlib.pyplot as plt
import seaborn as sns


def list_data_files():
    '''
    Lists the files contained in the data directory

    Output (list): Files in the data directory
    '''
    # Listing all of the files within the data folder
    current_directory = os.getcwd()
    data_directory = current_directory + '\\data\\'
    data_files = os.listdir(data_directory)
    
    # Adding the absolute filepath
    data_files_with_path = [os.path.join(data_directory, data_file) for data_file in data_files]
    
    return data_files_with_path


def combine_route_files(list_of_files):
    '''
    Reads each route description file and combines them to output one data frame containing all route description data
    
    Input (list): File names
    Output (dataframe): Route descriptions
    '''
    # Filtering to route files only
    route_files = [file for file in list_of_files if 'route' in file]
    
    # Collecting files by file type for knowing how to read them
    csv_files = [file for file in route_files if 'csv' in file]
    json_files = [file for file in route_files if 'json' in file and 'jsonlines' not in file]
    jsonlines_files = [file for file in route_files if 'jsonlines' in file]

    # Data frame to be filled and outputted
    route_descriptions = pd.DataFrame()

    # Looping through each file and adding it to the route_descriptions data frame
    for route_file in route_files:
        
        # Each type of file needs to be read differently
        if route_file in csv_files:
            state_routes = pd.read_csv(route_file)
            state_name = route_file.split('\\')[-1].replace('-routes.csv', '')
        if route_file in json_files:
            state_routes = pd.read_json(route_file)
            state_name = route_file.split('\\')[-1].replace('-routes.json', '')
        if route_file in jsonlines_files:
            state_routes = pd.read_json(route_file, lines=True)
            state_name = route_file.split('\\')[-1].replace('-routes.jsonlines', '')
        
        # Adding the state name as a column
        state_routes['State'] = state_name
        route_descriptions = route_descriptions.append(state_routes)

    return route_descriptions



def formatting_route_descriptions(route_descriptions):
    '''
    Extracting JSON from the route descriptions into their own columns

    Input (dataframe): Route descriptions for all states
    Output (dataframe): Formatted route descriptions
    '''
    # Specifying columns containing JSON to explode into their own columns
    json_columns = ['grade', 'type', 'metadata']
    
    # Looping through these columns to explode the JSON contents into their own columns and drop the original column
    for column in json_columns:
        try:
            print(f'Exploding columns for {column}')
            exploded_json = route_descriptions[column].apply(pd.Series)
            exploded_json = exploded_json.add_prefix(column+'_')
            route_descriptions = pd.concat([route_descriptions, exploded_json], sort=False, axis=1)
            route_descriptions = route_descriptions.drop(column, axis=1)
        except:
            print(f'Errors with the {column} column')
    
    # Extracting the latitude and longitude of the route
    try:
        print('Extracting the longitude/latitude')
        route_descriptions['Longitude'] = route_descriptions['metadata_parent_lnglat'].apply(lambda x: x[0])
        route_descriptions['Latitude'] = route_descriptions['metadata_parent_lnglat'].apply(lambda x: x[1])
        route_descriptions = route_descriptions.drop('metadata_parent_lnglat', axis=1)
    except:
        print('Unable to extract the latitude and longitude')
    
    # Adding the number of routes in the sector
    try:
        print('Adding the number of routes per sector')
        num_routes_in_sector = route_descriptions['metadata_mp_sector_id'].value_counts()
        route_descriptions = route_descriptions.merge(num_routes_in_sector.rename('num_routes_in_sector'),
                                                      left_on='metadata_mp_sector_id', right_index=True)
    except:
        print('Unable to calculate the number of routes in the sector')

    # Renaming some of the column names
    try:
        print('Renaming metadata columns')
        route_descriptions.columns = [column.replace('metadata_mp_', '').replace('metadata_', '') for column in route_descriptions.columns]
    except:
        print('Unable to renmae metadata columns')

    # Changing the state names to be more readable
    state_names = {'az': 'Arizona',
                   'ca': 'California',
                   'co': 'Colorado',
                   'idaho': 'Idaho',
                   'montana': 'Montana',
                   'nv': 'Nevada',
                   'oregon': 'Oregon',
                   'ut': 'Utah',
                   'wa': 'Washington'}

    route_descriptions['State'] = route_descriptions['State'].replace(state_names)

    route_descriptions.reset_index(drop=True, inplace=True)

    return route_descriptions


def read_route_descriptions():
    '''
    Reads the route description CSV if it exists, and formats one out of individual state route descriptions if not

    Output (dataframe): One row for each route for each state in the data folder
    '''
    data_files = list_data_files()
    route_file = [file for file in data_files if 'route_descriptions.csv' in file]  # Checking if the route file exists
    
    # Checking if the file exists, reading it if so
    if len(route_file) > 0:
        print('Compiled route descriptions found')
        route_descriptions = pd.read_csv(route_file[0])
    
    # Creating the route descriptions file if it does not exist
    else:
        print('No compiled route descriptions file found, compiling list from files in the data directory')
        combined_routes = combine_route_files(data_files)

        route_descriptions = formatting_route_descriptions(combined_routes)
        route_descriptions.to_csv('data\\route_descriptions.csv', index=False)
    
    return route_descriptions
