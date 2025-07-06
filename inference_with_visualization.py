import onnxruntime as ort
import cv2
import numpy as np
import matplotlib.pyplot as plt

def xywh2xyxy(x):
    """Convert bounding box from xywh to xyxy format"""
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2  # top left x
    y[..., 1] = x[..., 1] - x[..., 3] / 2  # top left y
    y[..., 2] = x[..., 0] + x[..., 2] / 2  # bottom right x
    y[..., 3] = x[..., 1] + x[..., 3] / 2  # bottom right y
    return y

def nms(boxes, scores, iou_threshold=0.45):
    """Apply Non-Maximum Suppression"""
    if len(boxes) == 0:
        return []
    
    boxes = boxes.astype(np.float32)
    scores = scores.astype(np.float32)
    
    # Get indices of boxes sorted by scores
    indices = np.argsort(scores)[::-1]
    
    keep = []
    while len(indices) > 0:
        current = indices[0]
        keep.append(current)
        
        if len(indices) == 1:
            break
            
        # Calculate IoU between current box and remaining boxes
        current_box = boxes[current]
        remaining_boxes = boxes[indices[1:]]
        
        # Calculate intersection
        x1 = np.maximum(current_box[0], remaining_boxes[:, 0])
        y1 = np.maximum(current_box[1], remaining_boxes[:, 1])
        x2 = np.minimum(current_box[2], remaining_boxes[:, 2])
        y2 = np.minimum(current_box[3], remaining_boxes[:, 3])
        
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        
        # Calculate union
        area_current = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
        area_remaining = (remaining_boxes[:, 2] - remaining_boxes[:, 0]) * (remaining_boxes[:, 3] - remaining_boxes[:, 1])
        union = area_current + area_remaining - intersection
        
        # Calculate IoU
        iou = intersection / union
        
        # Keep boxes with IoU less than threshold
        indices = indices[1:][iou <= iou_threshold]
    
    return keep

def postprocess_yolo_output(outputs, conf_threshold=0.5, iou_threshold=0.45):
    """Post-process YOLO output to get final detections"""
    predictions = outputs[0]
    
    # predictions shape: (batch_size, num_detections, 5 + num_classes)
    # For each detection: [x, y, w, h, confidence, class_scores...]
    
    detections = []
    
    for i in range(predictions.shape[0]):  # batch size
        pred = predictions[i]  # (num_detections, 5 + num_classes)
        
        # Extract box coordinates, confidence, and class scores
        boxes = pred[:, :4]  # x, y, w, h
        obj_conf = pred[:, 4]  # objectness confidence
        class_scores = pred[:, 5:]  # class scores
        
        # Get class with highest score for each detection
        class_ids = np.argmax(class_scores, axis=1)
        class_conf = np.max(class_scores, axis=1)
        
        # Calculate final confidence
        final_conf = obj_conf * class_conf
        
        # Filter by confidence threshold
        valid_mask = final_conf >= conf_threshold
        
        if np.sum(valid_mask) == 0:
            continue
            
        boxes = boxes[valid_mask]
        final_conf = final_conf[valid_mask]
        class_ids = class_ids[valid_mask]
        
        # Convert to xyxy format
        boxes = xywh2xyxy(boxes)
        
        # Apply NMS
        keep_indices = nms(boxes, final_conf, iou_threshold)
        
        for idx in keep_indices:
            detections.append({
                'bbox': boxes[idx],
                'confidence': final_conf[idx],
                'class_id': class_ids[idx]
            })
    
    return detections

def draw_detections(image, detections, class_names=None):
    """Draw bounding boxes and labels on image"""
    img_copy = image.copy()
    
    # Define colors for different classes
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
        (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
        (255, 192, 203), (173, 216, 230), (144, 238, 144), (255, 218, 185)
    ]
    
    for detection in detections:
        bbox = detection['bbox']
        confidence = detection['confidence']
        class_id = detection['class_id']
        
        # Get coordinates
        x1, y1, x2, y2 = bbox.astype(int)
        
        # Select color
        color = colors[class_id % len(colors)]
        
        # Draw bounding box
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        
        # Prepare label
        if class_names and class_id < len(class_names):
            label = f'{class_names[class_id]}: {confidence:.2f}'
        else:
            label = f'Class {class_id}: {confidence:.2f}'
        
        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(img_copy, (x1, y1 - label_size[1] - 10), 
                     (x1 + label_size[0], y1), color, -1)
        
        # Draw label text
        cv2.putText(img_copy, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return img_copy

def main():
    # Load ONNX model
    session = ort.InferenceSession('models/mahjong-yolom-best.onnx')
    
    # Get model input details
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    print(f"Model input shape: {input_shape}")
    
    # Load and preprocess image
    img_path = 'path/to/image.jpg'  # Replace with actual image path
    img = cv2.imread(img_path)
    
    if img is None:
        print(f"Error: Could not load image from {img_path}")
        return
    
    original_img = img.copy()
    img_height, img_width = img.shape[:2]
    
    # Preprocess image
    img_resized = cv2.resize(img, (640, 640))
    img_normalized = img_resized.astype(np.float32) / 255.0
    img_transposed = np.transpose(img_normalized, (2, 0, 1))
    img_batch = np.expand_dims(img_transposed, axis=0)
    
    # Run inference
    outputs = session.run(None, {input_name: img_batch})
    
    # Post-process outputs
    detections = postprocess_yolo_output(outputs, conf_threshold=0.5, iou_threshold=0.45)
    
    # Scale bounding boxes back to original image size
    scale_x = img_width / 640
    scale_y = img_height / 640
    
    for detection in detections:
        detection['bbox'][0] *= scale_x  # x1
        detection['bbox'][1] *= scale_y  # y1
        detection['bbox'][2] *= scale_x  # x2
        detection['bbox'][3] *= scale_y  # y2
    
    # Draw detections on original image
    result_img = draw_detections(original_img, detections)
    
    # Display results
    plt.figure(figsize=(12, 8))
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
    plt.title('Original Image')
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    plt.title(f'Detections ({len(detections)} found)')
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Save result
    cv2.imwrite('result_with_detections.jpg', result_img)
    print(f"Result saved to result_with_detections.jpg")
    print(f"Found {len(detections)} detections")

if __name__ == "__main__":
    main()