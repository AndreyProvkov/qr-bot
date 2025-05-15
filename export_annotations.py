import json
import os
from datetime import datetime
from pathlib import Path
import random
from typing import List, Dict, Any

from models import Annotation, Document, DocumentType, DocumentStatus
from db_viewer import get_db_session

def get_class_id(class_name: str) -> int:
    """Get class ID from class name."""
    class_mapping = {
        "stamp": 0,
        "text": 1,
        "table": 2,
        "graphic": 3,
        "empty_space": 4
    }
    return class_mapping.get(class_name, -1)

def create_coco_annotation(annotation: Annotation, image_id: int) -> Dict[str, Any]:
    """Convert our annotation to COCO format."""
    return {
        "id": annotation.id,
        "image_id": image_id,
        "category_id": get_class_id(annotation.class_name),
        "bbox": [
            annotation.x,
            annotation.y,
            annotation.width,
            annotation.height
        ],
        "area": annotation.width * annotation.height,
        "iscrowd": 0
    }

def create_coco_image(document: Document, image_id: int) -> Dict[str, Any]:
    """Create COCO image entry."""
    return {
        "id": image_id,
        "file_name": f"{document.id}.jpg",
        "width": document.width,
        "height": document.height,
        "date_captured": datetime.now().isoformat()
    }

def create_coco_categories() -> List[Dict[str, Any]]:
    """Create COCO categories list."""
    return [
        {"id": 0, "name": "stamp", "supercategory": "document"},
        {"id": 1, "name": "text", "supercategory": "document"},
        {"id": 2, "name": "table", "supercategory": "document"},
        {"id": 3, "name": "graphic", "supercategory": "document"},
        {"id": 4, "name": "empty_space", "supercategory": "document"}
    ]

def export_annotations(session, output_dir: str, split_ratio: Dict[str, float] = None):
    """Export annotations in COCO format."""
    if split_ratio is None:
        split_ratio = {"train": 0.7, "val": 0.15, "test": 0.15}
    
    # Get all documents with annotations
    documents = session.query(Document).filter(
        Document.status == DocumentStatus.PROCESSED
    ).all()
    
    # Shuffle documents
    random.shuffle(documents)
    
    # Split documents
    total = len(documents)
    train_end = int(total * split_ratio["train"])
    val_end = train_end + int(total * split_ratio["val"])
    
    splits = {
        "train": documents[:train_end],
        "val": documents[train_end:val_end],
        "test": documents[val_end:]
    }
    
    # Create COCO format for each split
    for split_name, split_docs in splits.items():
        coco_data = {
            "info": {
                "description": f"Document Layout Dataset - {split_name}",
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "QR Bot",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [{"id": 1, "name": "CC BY 4.0"}],
            "categories": create_coco_categories(),
            "images": [],
            "annotations": []
        }
        
        image_id = 1
        annotation_id = 1
        
        for doc in split_docs:
            # Add image
            coco_data["images"].append(create_coco_image(doc, image_id))
            
            # Add annotations
            for ann in doc.annotations:
                coco_ann = create_coco_annotation(ann, image_id)
                coco_ann["id"] = annotation_id
                coco_data["annotations"].append(coco_ann)
                annotation_id += 1
            
            image_id += 1
        
        # Save to file
        output_path = os.path.join(output_dir, f"annotations/{split_name}/instances_{split_name}.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, ensure_ascii=False, indent=2)

def main():
    session = get_db_session()
    try:
        export_annotations(session, "dataset")
        print("Annotations exported successfully!")
    finally:
        session.close()

if __name__ == "__main__":
    main() 