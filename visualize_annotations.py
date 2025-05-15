import os
import yaml
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm

def visualize_annotations():
    """Visualize YOLO annotations on images"""
    # Load dataset config
    with open("dataset_yolo/dataset.yaml", "r") as f:
        dataset_config = yaml.safe_load(f)
    
    # Create output directory
    output_dir = Path("visualization")
    output_dir.mkdir(exist_ok=True)
    
    # Colors for different classes
    colors = {
        0: (255, 0, 0),    # stamp - red
        1: (0, 255, 0),    # text - green
        2: (0, 0, 255),    # table - blue
        3: (255, 255, 0),  # graphic - yellow
        4: (255, 0, 255)   # empty_space - magenta
    }
    
    # Process each split
    splits = ["train", "val", "test"]
    for split in splits:
        print(f"\nVisualizing {split} split...")
        
        # Create split directory
        split_dir = output_dir / split
        split_dir.mkdir(exist_ok=True)
        
        # Get image and label paths
        images_dir = Path(dataset_config["path"]) / split / "images"
        labels_dir = Path(dataset_config["path"]) / split / "labels"
        
        # Process each image
        for img_path in tqdm(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")), 
                           desc=f"Visualizing {split} images"):
            # Read image
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"Error: Could not read image {img_path}")
                continue
            
            # Get image dimensions
            height, width = img.shape[:2]
            
            # Read corresponding label file
            label_path = labels_dir / f"{img_path.stem}.txt"
            if not label_path.exists():
                continue
            
            with open(label_path, "r") as f:
                lines = f.readlines()
            
            # Draw annotations
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                class_id = int(parts[0])
                x_center, y_center, w, h = map(float, parts[1:])
                
                # Convert YOLO format to pixel coordinates
                x1 = int((x_center - w/2) * width)
                y1 = int((y_center - h/2) * height)
                x2 = int((x_center + w/2) * width)
                y2 = int((y_center + h/2) * height)
                
                # Draw rectangle
                color = colors.get(class_id, (255, 255, 255))
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                # Add class label
                class_name = dataset_config["names"][class_id]
                cv2.putText(img, class_name, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Save visualization
            output_path = split_dir / f"{img_path.stem}_vis{img_path.suffix}"
            cv2.imwrite(str(output_path), img)
    
    print("\nVisualization completed!")
    print(f"Results saved in {output_dir}")

if __name__ == "__main__":
    visualize_annotations() 