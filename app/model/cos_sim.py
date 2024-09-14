# Import necessary dependencies
import os
import sys
import pathlib
import json
from typing import List, Dict, Tuple
from uuid import UUID

import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

import warnings
warnings.filterwarnings('ignore')

# Function to vectorize DataFrames
def vectorize(info: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorizes a given DataFrame by encoding experienceLevel numerically and applying one-hot encoding
    to categorical columns and multi-label binarization to language columns.

    Args:
        info (pd.DataFrame): A DataFrame containing user information with columns such as 'experienceLevel',
                             'role2', 'goal', 'trait', 'primaryLanguages', and 'secondaryLanguages'.

    Returns:
        pd.DataFrame: A vectorized DataFrame with numerical and one-hot encoded categorical columns.
    """

    if not info.empty:
        # Map experienceLevel to numerical values
        experience_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        info['experienceLevel'] = info['experienceLevel'].map(experience_map)

        # One-Hot Encoding for categorical columns
        categorical_cols = ['role2', 'goal', 'trait']
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
    
    return None

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
    all_columns = set()

    for table in tables:
        if table is None:
            continue
        else:
            all_columns = all_columns.union(set(table.columns))
    # all_columns = set().union(*[set(table.columns) for table in tables])

    # Add missing columns to each table and reorder columns
    aligned_tables = []

    for table in tables:
        if table is None:
            aligned_tables.append(None)
        else:
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
    vec_tables: Dict[str, pd.DataFrame],
    user_goal: str,
) -> Dict[str, pd.DataFrame]:
    """
    Computes the cosine similarity between a user vector and a set of role-based feature vectors,
    applying dynamic weighting based on the user's goal.

    Args:
        user_vector (pd.DataFrame): The vectorized DataFrame of the user's features.
        vec_tables (Dict[str, pd.DataFrame]): Dictionary of role-based feature vectors.
        user_goal (str): The goal of the user, which influences the weighting of experienceLevel.

    Returns:
        Dict[str, pd.DataFrame]: Sorted DataFrame by cosine similarity for each role.
    """

    role_similarity_results = {}

    # Weighting matrix for experienceLevel based on goal
    experience_weight = 1.0  # Default weight
    if user_goal == 'win hackathon':
        experience_weight = 2.0  # Prioritize experienceLevel for 'win hackathon'
    elif user_goal == 'gain experience':
        experience_weight = 1.5  # Moderate weight for experience matching

    # Identifier columns (you want to keep these but not use them in similarity computation)
    id_columns = ['id', 'userId', 'name', 'role1']  # Adjust based on your actual columns

    # Iterate over each role-based DataFrame
    for key, vec_table in vec_tables.items():
        if vec_table is not None:
            id_frame = vec_table[['id', 'userId', 'name', 'role1']]
            
            # Separate feature columns from identifier columns
            vec_table_features = vec_table.drop(columns=id_columns, errors='ignore')  # Use only feature columns
            vec_table_identifiers = vec_table[id_columns]  # Keep the identifier columns

            # Apply weight to experienceLevel column
            vec_table_features['experienceLevel'] *= experience_weight
            user_vector['experienceLevel'] *= experience_weight

            # Compute cosine similarity
            vec_table_vectors = vec_table_features.values
            user_vector_values = user_vector.drop(columns=id_columns, errors='ignore').values

            similarity_scores = cosine_similarity(user_vector_values, vec_table_vectors).flatten()

            # Add similarity scores to the DataFrame
            vec_table_features['similarity'] = similarity_scores
            vec_table_features = pd.concat([vec_table_features, id_frame], axis=1)

            # Sort by similarity
            sorted_table = vec_table_features.sort_values(by='similarity', ascending=True).reset_index(drop=True)

            role_similarity_results[key] = sorted_table
        else:
            role_similarity_results[key] = None

    return role_similarity_results

# Function to make all letters lowercase
def to_lowercase(x):
    # If the value is a string, convert it to lowercase
    if isinstance(x, str):
        return x.lower()
    # If the value is a list of strings, convert each element to lowercase
    elif isinstance(x, list):
        return [item.lower() if isinstance(item, str) else item for item in x]
    # If it's something else, return it unchanged
    return x

# Function to continue the workflow
def return_dummy(ds: pd.DataFrame, be: pd.DataFrame, fe: pd.DataFrame, bs: pd.DataFrame):
    return_list = []
    for df in [ds, be, fe, bs]:
        if df is None:
            return_list.append([])
        else:
            return_list.append(df.to_dict(orient='records'))

    return return_list

# FUNCTION TO GET RECOMMENDATIONS
def get_recommendations(info: Dict, allUsers: List[Dict]) -> Tuple[List[Dict]]:
    if not allUsers:
        return [], [], [], []
    
    # Create empty DataFrame for each role
    data_science = pd.DataFrame()
    backend = pd.DataFrame()
    frontend = pd.DataFrame()
    business = pd.DataFrame()

    # Put users in the correct role bucket
    for user in allUsers:
        data = pd.DataFrame([user])
        
        if data['role1'].iloc[0] == 'data science':
            data_science = pd.concat([data_science, data], ignore_index=True)
        elif data['role1'].iloc[0] == 'back-end':
            backend = pd.concat([backend, data], ignore_index=True)
        elif data['role1'].iloc[0] == 'front-end':
            frontend = pd.concat([frontend, data], ignore_index=True)
        elif data['role1'].iloc[0] == 'business':
            business = pd.concat([business, data], ignore_index=True)

    # List of role tables
    role_tables = [
        data_science.applymap(to_lowercase),
        backend.applymap(to_lowercase),
        frontend.applymap(to_lowercase),
        business.applymap(to_lowercase)
    ]

    # DataFrames of new tables used for vectorization
    vec_ds = pd.DataFrame()
    vec_be = pd.DataFrame()
    vec_fe = pd.DataFrame()
    vec_bs = pd.DataFrame()

    # Drop unnecessary columns
    for i, table in enumerate(role_tables):
        vec_table = table.drop(columns=['school', 'note', 'discordLink', 'imageLink'], errors='ignore')
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

    for table in vec_tables:
        if table is not None:
            reference_columns = table.columns

    # Convert the dictionary to Pandas DataFrame and get user's goal
    user = pd.DataFrame([info]).applymap(to_lowercase)
    userGoal = user['goal'].iloc[0]

    # Get the vector for the user
    userVector = align_single_user(
        user_vector=vectorize(info=user).drop(
            columns=['school', 'note', 'discordLink'],
            errors='ignore'
        ),
        reference_columns=reference_columns
    )

    # Compare cosine similarity between the user and rows with different primary roles
    sorted_similarity_tables = compare_cos_sim(
        user_vector=userVector,
        vec_tables=vec_dict,
        user_goal=userGoal
    )

    # Create output
    output = []

    for role, table in sorted_similarity_tables.items():
        if table is not None:
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
                        "id": matching_row['id'].values[0],
                        "userId": matching_row['userId'].values[0],
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
                        "discordLink": matching_row['discordLink'].values[0],
                        "imageLink": matching_row['imageLink'].values[0]
                    }
                )

            # Append the recommendations for each role to the output
            output.append(recommendations)
        else:
            output.append([])
        
    return output[0], output[1], output[2], output[3]

if __name__ == '__main__':
    # Define relative path
    current_dir = os.getcwd()
    project_dir = os.path.dirname(current_dir)
    sys.path.append(project_dir)

    USERDATA = pathlib.Path(os.path.join(project_dir, 'userInfo'))
    sys.path.append(USERDATA)
    
    # Read in the input and an example
    with open(os.path.join(USERDATA, 'rocco.json'), 'r') as file:
        info = json.load(file)

    with open(os.path.join(USERDATA, 'input.json'), 'r') as inFile:
        allUsers = json.load(inFile)

    # Test case
    info = {
        'id': UUID('c01f12d9-5da3-478f-bd30-f6e6c8130975'),
        'userId': UUID('0e70d649-c442-448d-b86f-e4dfbbcf8fbc'),
        'name': 'Vishak Vikranth',
        'experienceLevel': 'intermediate',
        'role1': 'back-end',
        'role2': 'data Science',
        'primaryLanguages': ['Python', 'Java', 'Go'],
        'secondaryLanguages': ['C/C++', 'SQL', 'R'],
        'school': 'The University of Alabama',
        'goal': None,
        'note': None,
        'trait': None,
        'discordLink': None,
        'imageLink': None
    }
    allUsers = [
        {
            'id': UUID('b14b2c7c-2a04-4f40-b79a-2a40e2b477ab'),
            'userId': UUID('56f597ed-e433-4063-9712-29728ba1769e'),
            'name': 'Vishak Vikranth',
            'experienceLevel': 'expert',
            'role1': 'back-end',
            'role2': 'data science',
            'primaryLanguages': ['C++', 'Python', 'Go'],
            'secondaryLanguages': ['JavaScript', 'MATLAB', 'R'],
            'school': 'THE UNIVERSITY OF ALABAMA',
            'goal': None,
            'note': None,
            'trait': None,
            'discordLink': None,
            'imageLink': None
        }
    ]

    # Get recommendations
    data_science_list, backend_list, frontend_list, business_list = get_recommendations(
        info=info,
        allUsers=allUsers
    )

    # Show results
    print("Teammates Recommendations:")
    print("Data Science:", data_science_list)
    print("Back-End:", backend_list)
    print("Front-End:", frontend_list)
    print("Business:", business_list)