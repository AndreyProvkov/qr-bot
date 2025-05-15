import os
import yaml
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm

def check_dataset():
    """Check dataset structure and annotations"""
    # Load dataset config
    with open("dataset_yolo/dataset.yaml", "r") as f:
        dataset_config = yaml.safe_load(f)
    
    # Check directories
    splits = ["train", "val", "test"]
    for split in splits:
        print(f"\nChecking {split} split...")
        
        # Check images directory
        images_dir = Path(dataset_config["path"]) / split / "images"
        if not images_dir.exists():
            print(f"Error: {images_dir} does not exist")
            return False
        
        # Check labels directory
        labels_dir = Path(dataset_config["path"]) / split / "labels"
        if not labels_dir.exists():
            print(f"Error: {labels_dir} does not exist")
            return False
        
        # Count files
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        label_files = list(labels_dir.glob("*.txt"))
        
        print(f"Found {len(image_files)} images and {len(label_files)} labels")
        
        if len(image_files) != len(label_files):
            print(f"Warning: Number of images ({len(image_files)}) does not match number of labels ({len(label_files)})")
        
        # Check annotations
        for img_path in tqdm(image_files, desc=f"Checking {split} annotations"):
            # Check image
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"Error: Could not read image {img_path}")
                continue
            
            # Check corresponding label
            label_path = labels_dir / f"{img_path.stem}.txt"
            if not label_path.exists():
                print(f"Warning: No label file for {img_path}")
                continue
            
            # Read and check label file
            with open(label_path, "r") as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    print(f"Error: Invalid label format in {label_path}")
                    continue
                
                class_id = int(parts[0])
                if class_id not in range(len(dataset_config["names"])):
                    print(f"Error: Invalid class ID {class_id} in {label_path}")
                    continue
                
                # Check coordinates
                coords = list(map(float, parts[1:]))
                if not all(0 <= x <= 1 for x in coords):
                    print(f"Warning: Coordinates out of range in {label_path}")
    
    print("\nDataset check completed!")
    return True

if __name__ == "__main__":
    check_dataset() 