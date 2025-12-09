import os

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_distances
from sklearn.model_selection import train_test_split
from tqdm import tqdm


class DatasetCreator:
    def __init__(self):
        """
        This class creates a dataset for prompt injection attacks.
        Prompt injection examples are taken from the HackaPrompt dataset.
        Usability examples are taken from the OpenAssistant dataset.
        
        Note: 'paraphrase-MiniLM-L6-v2' is used as the embedding model.
        """
        # download dataset or load from local
        if os.path.exists("data/hackaprompt.parquet"):
            df = pd.read_parquet("data/hackaprompt.parquet")
        else:
            df = pd.read_parquet("hf://datasets/hackaprompt/hackaprompt-dataset/hackaprompt.parquet")
            df.to_parquet("data/hackaprompt.parquet", index=False)
    
        df = df[df['expected_completion'] != "I have been PWNED"]
        df["prompt_injection"] = True
        df["text"] = df["user_input"]
        df = df[df['text'].str.len() > 30]
        df = df[["text", "prompt_injection"]]
        self.df_pi = df.drop_duplicates(subset=['text'], keep='first') # from 62.9k to ~37k

        
        # Load Embedding model
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        # calculate embeddings
        self.embeddings_pi = model.encode(
            self.df_pi['text'].tolist(), 
            batch_size=256, 
            show_progress_bar=True
        )
        
        df = pd.read_parquet("hf://datasets/OpenAssistant/oasst1/data/train-00000-of-00001-b42a775f407cee45.parquet")
        df = df[df['lang'].isin(['en', 'de'])]
        df = df[df['role'] == 'prompter']
        df["prompt_injection"] = False
        self.df_usability = df[["text", "prompt_injection"]]
        
        self.embeddings_usability = model.encode(
            self.df_usability['text'].tolist(), 
            batch_size=256, 
            show_progress_bar=True
        )
        
    def create_and_store_subset(self, n_samples):
        """
        Create a diverse subset with half prompt injection and half usability examples.
        
        1. Create a diverse subset of the prompt injection dataset.
        2. Create a diverse subset of the usability dataset.
        3. Split both datasets into train, test, and validation sets.
        4. Combine the datasets into a single dataset.
        5. Store the datasets in parquet format.
        
        Parameters:
        n_samples (int): The number of samples in the dataset to be created.
        """
        self.n_samples = n_samples
        samples_pi = int(n_samples * .5)
        samples_usability = n_samples - samples_pi
        
        # log to file
        # with open("data/combined.log", "a") as f:
        #     f.write(f"Creating dataset with {n_samples} samples.\n")
        #     f.write(f"Prompt injection samples: {samples_pi}\n")
        #     f.write(f"Usability samples: {samples_usability}\n")

        # store to file
        # with open("data/combined.log", "a") as f:
        #     f.write("Starting Prompt Injection subset creation...\n")
        df_pi_diverse = self.create_diverse_subset(samples_pi, self.df_pi, self.embeddings_pi)        
        # with open("data/combined.log", "a") as f:
        #     f.write("Starting Usability subset creation...\n")
        df_usability_diverse = self.create_diverse_subset(samples_usability, self.df_usability, self.embeddings_usability)
        
        tr, te, val = self.split_to_train_test_val(df_pi_diverse)
        tr2, te2, val2 = self.split_to_train_test_val(df_usability_diverse)
        train, test, val = self.combine_datasplits([tr, te, val], [tr2, te2, val2])
        
        self.store_dataset(train, n_samples, "train")
        self.store_dataset(test, n_samples, "test")
        self.store_dataset(val, n_samples, "val")
    
    def create_diverse_subset(self, n_samples, df, embeddings):
        """
        Create a diverse subset of the dataset using a greedy algorithm.
        
        1. Choose a random starting point.
        2. For each subsequent point, choose the one that is furthest away from all previously selected points.
        3. Repeat until the desired number of samples is reached.
        
        Parameters:
        n_samples (int): The number of samples to select.
        df (pd.DataFrame): The dataframe to select samples from.
        embeddings (np.ndarray): The embeddings of the dataframe.
        """
        distance_matrix = cosine_distances(embeddings)
        selected_indices = []

        # 1. Startpunkt zufällig wählen
        np.random.seed(42)
        start_idx = np.random.choice(len(df))
        selected_indices.append(start_idx)

        # 2. Greedy Auswahl
        available_indices = set(range(len(df))) - set(selected_indices)

        for i in tqdm(range(n_samples - 1)):
            dists_to_selected = distance_matrix[list(available_indices)][:, selected_indices]
            # Minimum Abstand zu allen bisher ausgewählten
            min_dists = dists_to_selected.min(axis=1)
            # with open("data/combined.log", "a") as f:
            #     f.write(f"{i}: {np.max(min_dists)}\n")
            # Wähle den Punkt mit größtem Mindestabstand
            next_idx_relative = np.argmax(min_dists)
            next_idx = list(available_indices)[next_idx_relative]
            selected_indices.append(next_idx)
            available_indices.remove(next_idx)

        df_most_diverse = df.iloc[selected_indices]
        return df_most_diverse
    
    def store_dataset(self, df, n_samples, identifier):
        """
        Store the dataset in parquet format.
        Parameters:
        df (pd.DataFrame): The dataframe to store.
        n_samples (int): The number of samples in the dataset.
        identifier (str): The identifier for the dataset which will be appended to path.
        """
        output_path = f"data/combined-{n_samples}-diverse/{identifier}.parquet"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)
        
    def split_to_train_test_val(self, df):
        """
        Split the dataset into train, test, and validation sets.
        Parameters:
        df (pd.DataFrame): The dataframe to split.
        """
        
        train, df_temp = train_test_split(df, test_size=0.2, random_state=42)
        test, val = train_test_split(df_temp, test_size=0.5, random_state=42)
        return train, test, val
    
    def combine_datasplits(self, sets1, sets2):
        """
        Combine to sets of train, test, and validation sets into one combined train, test and validation set.
        Parameters:
        sets1 (list): The first set of train, test, val.
        sets2 (list): The second set of train, test, val.
        """
        df_comb = []
        for df1, df2 in zip(sets1, sets2):
            temp = pd.concat([df1, df2])
            temp = temp.sample(frac=1) # shuffle combined data
            df_comb.append(temp)
        return df_comb[0], df_comb[1], df_comb[2]

            