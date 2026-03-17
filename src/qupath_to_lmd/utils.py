import ast
import itertools
import re
import string
from random import sample

import geopandas
import numpy as np
import pandas
import pandas as pd
import streamlit as st
from loguru import logger

def generate_combinations(list1, list2, num) -> list:
   """Generate dictionary from all combinations of two lists and a range, assigning arbitrary values."""
   logger.info("Created combinations")
   assert isinstance(list1, list) and all(isinstance(i, str) for i in list1), "Input 1 must be a list of strings"
   assert isinstance(list2, list) and all(isinstance(i, str) for i in list2), "Input 2 must be a list of strings"
   assert isinstance(num, int) and num > 0, "Input 3 must be a positive integer"
   keys = [f"{a}_{b}_{i}" for a, b, i in itertools.product(list1, list2, range(1, num + 1))]
   return keys

def create_list_of_acceptable_wells(
      plate:str="384", 
      margins:int=0,
      step_row:int=1,
      step_col:int=1,
      tube_count:int=5): # Added tube count parameter
   """Creates wells or tubes according to user parameters."""
   logger.info(f"Creating list of acceptable targets for: {plate}")
   
   if plate == "Tubes":
      # Generates A, B, C, D, E etc. based on how many caps you have
      return list(string.ascii_uppercase[:tube_count])

   if plate not in ["384","96"]:
      raise ValueError("Plate must be either 384 or 96")
   if not isinstance(margins,int):
      raise ValueError("margins must be an integer")

   min_row = 1
   min_col = 1
   max_row = 16 if plate == "384" else 8
   max_col = 24 if plate == "384" else 12

   if margins>0 :
      max_col += -(margins)
      max_row += -(margins)
      min_col += margins
      min_row += margins

   list_of_acceptable_wells = []
   for row in list(string.ascii_uppercase[min_row-1 : max_row : step_row]):
      for column in range(min_col , max_col+1, step_col):
         list_of_acceptable_wells.append(str(row) + str(column))

   return list_of_acceptable_wells

def sample_placement():
   """Sample placement into plate or tube csv."""
   logger.info("Sample placement for CSV export")

   plate_type = "384"  
   if 'plate_gen_params' in st.session_state and isinstance(st.session_state.plate_gen_params, dict):
      plate_type = st.session_state.plate_gen_params.get('plate_type', "384")

   if plate_type == "Tubes":
      # Simple 2-column CSV for tubes
      df = pandas.DataFrame(list(st.session_state.saw.items()), columns=["Sample", "Target"])
      return df

   max_row = 16 if plate_type == "384" else 8
   max_col = 24 if plate_type == "384" else 12

   rows= [i for i in string.ascii_uppercase[:max_row]]
   columns = [str(i) for i in range(1,max_col+1)]
   df = pandas.DataFrame('',columns=columns, index=rows)

   for i in st.session_state.saw.keys():
      location = st.session_state.saw[i]
      df.at[location[0],location[1:]] = i

   return df

def create_dataframe_samples_wells(
      acceptable_wells_list:list = None,
      randomize:bool = False,
      plate_string:str = "384",
      ):
   """Creates a dataframe to be displayed."""
   
   if plate_string == "Tubes":
      tube_names = acceptable_wells_list if acceptable_wells_list else list(string.ascii_uppercase[:4])
      if st.session_state.view_mode == "default":
         df = pd.DataFrame(tube_names, index=tube_names, columns=["Target Cap"])
      elif st.session_state.view_mode == "samples":
         list_of_classes = list(set(st.session_state.gdf['classification_name'].values)) if st.session_state.gdf is not None else []
         df = pd.DataFrame(np.nan, index=tube_names, columns=["Sample"], dtype=object)
         if randomize:
            tube_names = sample(tube_names, len(tube_names))
         for s, tube in zip(list_of_classes, tube_names):
            df.at[tube, "Sample"] = s
      return df

   # Original Plate Logic below
   rows, cols = (16, 24) if plate_string == "384" else (8, 12)

   if st.session_state.view_mode == "default":
      row_labels = list(string.ascii_uppercase[:rows])
      col_labels = list(range(1, cols + 1))
      plate_data = [[f"{r}{c}" for c in col_labels] for r in row_labels]
      df = pd.DataFrame(plate_data, index=row_labels, columns=col_labels)

   elif st.session_state.view_mode == "samples": 
      if st.session_state.gdf is None:
         st.error("GeoDataFrame not found. Please upload a GeoJSON file first.")
         st.stop()

      list_of_classes = list(set(st.session_state.gdf['classification_name'].values))
      df = pd.DataFrame(np.nan, index=list(string.ascii_uppercase[:rows]), columns=range(1, cols + 1), dtype=object)

      if len(list_of_classes) > len(acceptable_wells_list):
         st.warning("More classes than allowed wells")

      if randomize:
         acceptable_wells_list = sample(acceptable_wells_list, len(acceptable_wells_list))

      for s, well in zip(list_of_classes, acceptable_wells_list):
         df.at[well[0], int(well[1:])] = s

   return df

def provide_highlighting_for_df(acceptable_wells_set:set = None):
   """Creates map to color dataframe."""
   if st.session_state.view_mode == "default":
      def highlight_selected(well_name):
         if well_name in acceptable_wells_set:
            return 'background-color: #77dd77; color: black;' # Green
         else:
            return 'background-color: #f0f2f6;' # Light gray
      return highlight_selected

   elif st.session_state.view_mode == "samples":
      list_of_classes = set(st.session_state.gdf['classification_name'].values)
      def highlight_selected(well_name):
            if well_name in list_of_classes:
               return 'background-color: #77dd77; color: black;' # Green
            else:
               return 'background-color: #f0f2f6;' # Light gray
      return highlight_selected

def parse_dictionary_from_file(file_input) -> dict:
   """Reads a file supposed to contain a Python dictionary and parses it."""
   logger.info("Parse external txt file to python dictionary")
   content = ""
   try:
      # Check if it's a string path (from Jupyter/testing)
      if isinstance(file_input, str):
         with open(file_input, 'r', encoding='utf-8-sig') as f:
            content = f.read()
      # Check if it's a file-like object (from st.file_uploader)
      elif hasattr(file_input, 'read'):
         # read() returns bytes, so we need to decode it to a string
         content = file_input.read().decode('utf-8-sig')
      else:
         logger.error(f"Unsupported input type for parsing: {type(file_input)}")
         return {}

   except Exception as e:
      logger.error(f"Error reading file content: {e}")
      return {}

   # Remove comments and strip whitespace
   # content = re.sub(r'#.*', '', content)
   # content = content.strip()

   if not content:
      return {}

   try:
      # ast.literal_eval is safe and handles many Python literal formats
      return ast.literal_eval(content)
   except (ValueError, SyntaxError) as e:
      logger.error(f"Failed to parse dictionary from content: {e}")
      return {}

def extract_coordinates(geometry):
      if geometry.geom_type == 'Polygon':
         return [list(coord) for coord in geometry.exterior.coords]
      elif geometry.geom_type == 'LineString':
         return [list(coord) for coord in geometry.coords]
      else:
         st.write(f'Geometry type {geometry.geom_type} not supported, please convert to Polygon or LineString in Qupath')
         st.stop()

def dataframe_to_saw_dict(df: pd.DataFrame) -> dict:
    """Converts the layout DataFrame to a samples-and-wells dictionary."""
    saw_dict = {}
    for row_idx, series in df.iterrows():
        for col_idx, sample_name in series.items():
            if sample_name and pd.notna(sample_name):
                # If it is a Tube, the index itself (A, B, C) is the target
                plate_type = st.session_state.get('plate_gen_params', {}).get('plate_type', "384")
                if plate_type == "Tubes":
                    saw_dict[sample_name] = str(row_idx)
                else:
                    saw_dict[sample_name] = f"{row_idx}{col_idx}"
    return saw_dict

def update_classification_column(gdf:geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
   """Updates the 'classification' dictionary for every row.

   It replaces the value associated with the 'name' key inside the
   'classification' dictionary with the string value from the
   'classification_name' column.
   """
   logger.info("Updating classification of objects according to class split")

   def update_row_dict(row):
      if isinstance(row['classification'],dict):
         class_dict = row['classification']
      elif isinstance(row['classification'],str):
         class_dict = ast.literal_eval(row['classification'])

      class_dict['name'] = row['classification_name']

      row['classification'] = str(class_dict)

      return row['classification']

   gdf['classification'] = gdf.apply(update_row_dict, axis=1)

   return gdf


def sanitize_gdf(gdf):
   """Ensure compatibility with QuPath."""
   logger.info("Dropping columns with NaNs in the geodataframe")
   #check for NaNs (they cause error with QuPath)
   # drop columns if they exist
   gdf = gdf.dropna(axis="columns")

   #ensure critical columns there
   cols_to_keep = ['id',"objectType","classification","geometry"]
   # Check that all critical columns are present
   missing = [col for col in cols_to_keep if col not in gdf.columns]
   if missing:
      logger.error(f"Missing critical columns: {missing}")
      raise ValueError(f"Missing critical columns: {missing}")

   return gdf[cols_to_keep]

