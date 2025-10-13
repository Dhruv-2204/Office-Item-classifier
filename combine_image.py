from PIL import Image
import random, os

# Add your own path as argument 

# simple synthetic scene builder example
from PIL import Image
import random, os

def combine_images(
    images_folder, 
    output_folder, 
    num_scenes=50, 
    scene_size=(512, 512), 
    min_obj_size=200, 
    max_obj_size=400, 
    max_overlap=0.15
):
    """
    Create synthetic multi-object images from single-object labeled images.
    
    Parameters:
      images_folder: path to folder containing source images
      output_folder: where to save composite images
      num_scenes: number of composite images to create
      scene_size: (width, height) of the output image
      min_obj_size / max_obj_size: random object size range
      max_overlap: allowed IoU between placed objects (0–1)
    """
    os.makedirs(output_folder, exist_ok=True)
    images = [os.path.join(images_folder, f) for f in os.listdir(images_folder) if f.lower().endswith(('.jpg', '.png'))]

    def boxes_overlap(box1, box2):
        """Check IoU between two bounding boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        xi1, yi1 = max(x1, x2), max(y1, y2)
        xi2, yi2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        union_area = w1*h1 + w2*h2 - inter_area
        return inter_area / union_area if union_area else 0

    for i in range(num_scenes):
        bg = Image.new('RGB', scene_size, (255, 255, 255))
        placed_boxes = []

        # choose 3–5 random images per scene
        used = random.sample(images, random.randint(3, 5))

        for img_path in used:
            obj = Image.open(img_path).convert("RGBA")
            scale = random.randint(min_obj_size, max_obj_size)
            obj = obj.resize((scale, scale))

            # find non-overlapping position
            for _ in range(100):
                x = random.randint(0, scene_size[0] - scale)
                y = random.randint(0, scene_size[1] - scale)
                box = (x, y, scale, scale)
                if all(boxes_overlap(box, b) < max_overlap for b in placed_boxes):
                    placed_boxes.append(box)
                    bg.paste(obj, (x, y), obj)
                    break

        bg.convert("RGB").save(os.path.join(output_folder, f"scene_{i+1}.jpg"))
        print(f"✅ Created scene_{i+1}.jpg with {len(placed_boxes)} objects")

    print("🎉 Finished creating synthetic multi-object images!")

# Example usage
combine_images(
    images_folder=r"C:\Users\dylan\Documents\Computer science\Computer Science Year 3\Image identification v2\images\All images",
    output_folder=r"C:\Users\dylan\Documents\Computer science\Computer Science Year 3\Image identification v2\images\Combined images",
    num_scenes=50,
    scene_size=(512, 512),
    min_obj_size=200,
    max_obj_size=400,
    max_overlap=0.1
)

