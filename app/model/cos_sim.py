# Import necessary dependencies
import os
import sys
import pathlib
import json
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity, cosine_distances

import warnings
warnings.filterwarnings('ignore')

# Function to vectorize DataFrames
def vectorize(info: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorizes a given DataFrame by applying one-hot encoding to categorical columns and multi-label binarization
    to language columns.

    This function processes the following columns:
    - One-hot encodes the categorical columns: 'experienceLevel', 'role2', 'goal', 'trait'.
    - Applies `MultiLabelBinarizer` to 'primaryLanguages' and 'secondaryLanguages' (which contain lists of languages).
    - Concatenates the one-hot encoded and binarized columns with the rest of the DataFrame.

    Args:
        info (pd.DataFrame): A DataFrame containing user information with columns such as 'experienceLevel',
                             'role2', 'goal', 'trait', 'primaryLanguages', and 'secondaryLanguages'.

    Returns:
        pd.DataFrame: A vectorized DataFrame with one-hot encoded categorical columns and binarized language columns.
                      The original 'primaryLanguages' and 'secondaryLanguages' columns are replaced with the 
                      respective binarized columns, and other columns remain unchanged.
    """

    # One-Hot Encoding for categorical columns
    categorical_cols = ['experienceLevel', 'role2', 'goal', 'trait']
    df_encoded = pd.get_dummies(info, columns=categorical_cols)

    # Use MultiLabelBinarizer for primaryLanguages & secondaryLanguages (lists of programming languages)
    mlb_primary = MultiLabelBinarizer()
    primary_languages_encoded = mlb_primary.fit_transform(info['primaryLanguages'])
    mlb_secondary = MultiLabelBinarizer()
    secondary_languages_encoded = mlb_secondary.fit_transform(info['secondaryLanguages'])

    # Convert to DataFrame with the correct column names for primaryLanguages & secondaryLanguages
    primary_languages_df = pd.DataFrame(
        primary_languages_encoded,
        columns=[f'primary_{lang}' for lang in mlb_primary.classes_]
    )
    secondary_languages_df = pd.DataFrame(
        secondary_languages_encoded,
        columns=[f'secondary_{lang}' for lang in mlb_secondary.classes_]
    )

    # Concatenate the encoded primary and secondary languages with the original DataFrame
    vectorizedinfo = pd.concat(
        [
            df_encoded.drop(columns=['primaryLanguages', 'secondaryLanguages']),
            primary_languages_df,
            secondary_languages_df
        ],
        axis=1
    )

    return vectorizedinfo

# Function to align columns across differnt DataFrames
def align_columns(tables: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Aligns the columns across multiple DataFrames by adding missing columns and ensuring column order consistency.

    This function takes a list of DataFrames and:
    - Identifies all unique columns across the given tables.
    - For each DataFrame, it adds any missing columns with default values (set to 0).
    - Reorders the columns in each DataFrame to maintain consistent column order across all tables.

    Args:
        tables (List[pd.DataFrame]): A list of DataFrames that need to have aligned columns.

    Returns:
        List[pd.DataFrame]: A list of DataFrames with aligned columns, where missing columns have been added
                            with default values of 0, and all DataFrames share the same column order.
    """

    # Get all unique columns across all tables
    all_columns = set().union(*[set(table.columns) for table in tables])

    # Add missing columns to each table and reorder columns
    aligned_tables = []

    for table in tables:
        missing_cols = all_columns - set(table.columns)
        for col in missing_cols:
            table[col] = 0  # Add missing columns with value 0
        table = table.reindex(sorted(all_columns), axis=1)  # Reorder columns to ensure consistency
        aligned_tables.append(table)

    return aligned_tables

# Function to align a single user's vector with the aligned DataFrames
def align_single_user(user_vector: pd.DataFrame, reference_columns: pd.Index) -> pd.DataFrame:
    """
    Aligns a single user's vector with a set of reference columns from a DataFrame.

    This function takes a single user's vector (as a DataFrame) and ensures that it has the same columns
    as the reference DataFrame by:
    - Adding any missing columns with default values of 0.
    - Reordering the columns to match the order of the reference DataFrame.

    Args:
        user_vector (pd.DataFrame): The user's data as a DataFrame that needs to be aligned with reference columns.
        reference_columns (pd.Index): The reference set of columns to align the user's vector with.

    Returns:
        pd.DataFrame: The user's vector with missing columns added (set to 0) and the columns reordered
                      to match the reference columns.
    """

    # Identify missing columns
    missing_cols = set(reference_columns) - set(user_vector.columns)
    
    # Add missing columns with default value 0
    for col in missing_cols:
        user_vector[col] = 0

    # Ensure the order of columns matches the reference DataFrame
    user_vector = user_vector.reindex(sorted(reference_columns), axis=1)

    return user_vector

# Function to compute least cosine similarity and sort by similarity score for each role
def compare_cos_sim(
    user_vector: pd.DataFrame,
    vec_tables: Dict[str, pd.DataFrame]
) -> Dict[str, pd.DataFrame]:
    """
    Computes the least cosine similarity between a user vector and a set of role-based 
    feature vectors, then sorts each role's feature vectors by their similarity to 
    the user vector in ascending order (least similar first).

    Args:
        user_vector (pd.DataFrame): A DataFrame containing the user's vector, 
            including both feature columns and identifier columns (e.g., 'userId', 
            'name', 'role1').
        vec_tables (Dict[str, pd.DataFrame]): A dictionary where each key represents 
            a role (e.g., 'role1', 'role2'), and each value is a DataFrame containing 
            feature vectors of individuals with that role. The DataFrames should also 
            contain identifier columns.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary where each key corresponds to a role, 
            and each value is a DataFrame. Each DataFrame contains the original 
            identifier columns, the feature vectors, and an additional 'similarity' 
            column representing cosine similarity between the user's vector and the 
            feature vectors. The DataFrames are sorted in ascending order of similarity 
            (i.e., least similar entries come first).
    
    Notes:
        - The `id_columns` variable contains column names such as 'userId', 'name', 
          and 'role1', which are identifiers and will be excluded from similarity 
          calculations.
        - Cosine similarity is computed using only the feature columns, and the results 
          are added to the DataFrame as a 'similarity' column.
        - The resulting DataFrames for each role are sorted by similarity score in 
          ascending order (least similar first) and then returned in the dictionary.
    """

    role_similarity_results = {}

    # Identifier columns (you want to keep these but not use them in similarity computation)
    id_columns = ['userId', 'name', 'role1']  # Adjust based on your actual columns

    # Iterate over each role-based DataFrame
    for key, vec_table in vec_tables.items():
        # Separate feature columns from identifier columns
        vec_table_features = vec_table.drop(columns=id_columns, errors='ignore')  # Use only feature columns
        vec_table_identifiers = vec_table[id_columns]  # Keep the identifier columns

        # Compute cosine similarity between the user vector and each row in the current table (features)
        vec_table_vectors = vec_table_features.values  # Get the feature vectors as a matrix
        user_vector_values = user_vector.drop(columns=id_columns, errors='ignore').values  # Ensure user_vector is in the correct format

        # Calculate cosine similarity
        similarity_scores = cosine_similarity(user_vector_values, vec_table_vectors).flatten()

        # Add similarity scores as a new column to the feature table (but not identifiers yet)
        vec_table_features['similarity'] = similarity_scores

        # Sort the feature table by the similarity score in ascending order (least similar first)
        sorted_table_features = vec_table_features.sort_values(by='similarity', ascending=True).reset_index(drop=True)

        # Use the sorted indices to reorder the identifiers
        sorted_table_identifiers = vec_table_identifiers.loc[sorted_table_features.index].reset_index(drop=True)

        # Concatenate identifiers and sorted similarity features back together
        sorted_table = pd.concat([sorted_table_identifiers, sorted_table_features], axis=1)

        # Store the sorted DataFrame in the result dictionary
        role_similarity_results[key] = sorted_table

    return role_similarity_results

# FUNCTION TO GET RECOMMENDATIONS
def get_recommendations(info: Dict, allUsers: List[Dict]) -> Tuple[List[Dict]]:
    """
    Generates role-based user recommendations by calculating the cosine similarity 
    between a given user and all other users across different roles, then returns 
    a list of recommendations sorted by similarity for each role.

    Args:
        info (Dict): A dictionary containing information about the current user, 
            including their profile data (such as role, experience level, etc.).
        allUsers (List[Dict]): A list of dictionaries where each dictionary represents 
            a user, containing user information such as roles, languages, goals, and traits.

    Returns:
        Tuple[List[Dict]]: A tuple containing four lists of dictionaries, each list 
            representing recommended users for the roles 'data science', 'back-end', 
            'front-end', and 'business'. Each dictionary in the list contains 
            information about the recommended user, such as name, experience level, 
            roles, languages, school, goal, and more.
    
    Notes:
        - The function first categorizes all users into their respective roles ('data science', 
          'back-end', 'front-end', and 'business').
        - Then it vectorizes user data (dropping unnecessary columns) to calculate 
          the cosine similarity between the target user and all other users in each role.
        - The `compare_cos_sim` function is used to compute the similarity and return 
          sorted recommendations for each role.
        - The final output is a tuple containing four lists of recommendations, one for each role.
    """
    
    # Create empty DataFrame for each role
    data_science = pd.DataFrame()
    backend = pd.DataFrame()
    frontend = pd.DataFrame()
    business = pd.DataFrame()

    # Put users in the correct role bucket
    for user in allUsers:
        data = pd.DataFrame([user])
        if user['role1'] == 'data science':
            data_science = pd.concat([data_science, data], ignore_index=True)
        elif user['role1'] == 'back-end':
            backend = pd.concat([backend, data], ignore_index=True)
        elif user['role1'] == 'front-end':
            frontend = pd.concat([frontend, data], ignore_index=True)
        elif user['role1'] == 'business':
            business = pd.concat([business, data], ignore_index=True)

    # List of role tables
    role_tables = [data_science, backend, frontend, business]

    # DataFrames of new tables used for vectorization
    vec_ds = pd.DataFrame()
    vec_be = pd.DataFrame()
    vec_fe = pd.DataFrame()
    vec_bs = pd.DataFrame()

    # Drop unnecessary columns
    for i, table in enumerate(role_tables):
        vec_table = table.drop(columns=['school', 'note', 'discordLink'], errors='ignore')
        if i == 0:
            vec_ds = vec_table
        elif i == 1:
            vec_be = vec_table
        elif i == 2:
            vec_fe = vec_table
        elif i == 3:
            vec_bs = vec_table

    # List of tables used for vectorization
    vec_tables = [vec_ds, vec_be, vec_fe, vec_bs]

    # Vectorize all users in all tables
    vec_tables = align_columns([vectorize(table) for table in vec_tables])

    vec_dict = {
        "data science": vec_tables[0],
        "back-end": vec_tables[1],
        "front-end": vec_tables[2],
        "business": vec_tables[3]
    }

    # Convert the dictionary to Pandas DataFrame
    info = pd.DataFrame([info])

    # Get the vector for the user
    userVector = align_single_user(
        user_vector=vectorize(info=info).drop(
            columns=['school', 'note', 'discordLink'],
            errors='ignore'
        ),
        reference_columns=vec_tables[0].columns
    )

    # Compare cosine similarity between the user and rows with different primary roles
    sorted_similarity_tables = compare_cos_sim(
        user_vector=userVector,
        vec_tables=vec_dict
    )

    # Create output
    output = []

    for role, table in sorted_similarity_tables.items():
        recommendations = []

        for i, row in table.iterrows():
            id = row['userId']
            
            if role == 'data science':
                matching_row = data_science[data_science['userId'] == id]
            elif role == 'back-end':
                matching_row = backend[backend['userId'] == id]
            elif role == 'front-end':
                matching_row = frontend[frontend['userId'] == id]
            elif role == 'business':
                matching_row = business[business['userId'] == id]
                
            recommendations.append(
                {
                    # "userId": matching_row['userId'].iloc[0],
                    "name": matching_row['name'].values[0],
                    "experienceLevel": matching_row['experienceLevel'].values[0],
                    "role1": matching_row['role1'].values[0],
                    "role2": matching_row['role2'].values[0],
                    "primaryLanguages": matching_row['primaryLanguages'].values[0],
                    "secondaryLanguages": matching_row['secondaryLanguages'].values[0],
                    "school": matching_row['school'].values[0],
                    "goal": matching_row['goal'].values[0],
                    "note": matching_row['note'].values[0],
                    "trait": matching_row['trait'].values[0],
                    "discordLink": matching_row['discordLink'].values[0]
                }
            )

        # Append the recommendations for each role to the output
        output.append(recommendations)

    return output[0], output[1], output[2], output[3]

if __name__ == '__main__':
    # Define relative path
    current_dir = os.getcwd()
    project_dir = os.path.dirname(current_dir)

    USERDATA = pathlib.Path(os.path.join(project_dir, 'userInfo'))
    
    # Read in the input and an example
    with open(os.path.join(USERDATA, 'rocco.json'), 'r') as file:
        example = json.load(file)

    with open(os.path.join(USERDATA, 'input.json'), 'r') as inFile:
        allUsers = json.load(inFile)

    # Get recommendations
    data_science_list, backend_list, frontend_list, business_list = get_recommendations(
        info=example,
        allUsers=allUsers
    )

    # Show results
    print("Teammates Recommendations:")
    print("Data Science:", data_science_list)
    print("Back-End:", backend_list)
    print("Front-End:", frontend_list)
    print("Business:", business_list)