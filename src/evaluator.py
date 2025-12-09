import asyncio
import os

import pandas as pd

from src.model import ClassifierModel
from src.utils.asyncio_utils import asyncio_limit_requests


class ModelEvaluator:
    def __init__(self, validation_set_path: str = "data/combined-1000-diverse/val.parquet"):
        self.validation_set = pd.read_parquet(validation_set_path)
        self.validation_set_path = validation_set_path
        
    async def generate_predictions(self, model: ClassifierModel) -> None:
        tasks = [self.get_response(model, text) for text in self.validation_set['text']]
        self.validation_set['predictions'] = await asyncio.gather(*tasks)
        
    @asyncio_limit_requests(limit=10)
    async def get_response(self, model: ClassifierModel, text: str) -> bool:
        response = model.classify_text(text)
        assert response is not None, f"Model returned None for text: {text}"
        return response
        
    async def evaluate_classifier(self, model: ClassifierModel) -> dict:
        
        await self.generate_predictions(model)       
        
        tp = ((self.validation_set['predictions'] == True) & (self.validation_set['prompt_injection'] == True)).sum()
        fp = ((self.validation_set['predictions'] == True) & (self.validation_set['prompt_injection'] == False)).sum()
        tn = ((self.validation_set['predictions'] == False) & (self.validation_set['prompt_injection'] == False)).sum()
        fn = ((self.validation_set['predictions'] == False) & (self.validation_set['prompt_injection'] == True)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2  / ((1/precision) + (1/recall)) if precision > 0 and recall > 0 else 0
                
        result = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        }
        
        self.store_results(model, result)

        return result
        
    def store_results(self, model: ClassifierModel, result: dict):
        path = "results/prompt_injection_classifier/results.csv"
        os.makedirs(os.path.dirname(path), exist_ok=True)

        result_str = f"{self.validation_set_path},{model.name},{result['precision']:.2f},{result['recall']:.2f},{result['f1']:.2f},{result['tp']},{result['fp']},{result['tn']},{result['fn']}\n"
        if not os.path.exists(path):
            with open(path, 'w') as file:
                file.write("dataset,model,precision,recall,f1,tp,fp,tn,fn\n")
                file.write(result_str)
        else:
            # only if dataset, model are not already in the file
            with open(path, 'r') as file:
                lines = file.readlines()
                if any(f"{self.validation_set_path},{model.name}" in line for line in lines):
                    print(f"Results for {model.name} on {self.validation_set_path} already exist.")
                    return                    
            with open(path, 'a') as file:        
                file.write(result_str)
        
        