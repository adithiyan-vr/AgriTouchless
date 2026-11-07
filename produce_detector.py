"""
produce_detector.py
AgriTouchless: Farm & Kitchen Hygiene Controller
Computer Vision Fruit & Vegetable Object Identifier & Weight Estimator
"""

import math
import time
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np


class ProduceItem:
    """Represents a classified fruit, vegetable item, or foreign object."""
    def __init__(self, name: str, category: str, base_weight_g: float,
                 confidence: float, color_bgr: Tuple[int, int, int], bbox: Tuple[int, int, int, int],
                 is_verified_produce: bool = True):
        self.name = name
        self.category = category
        self.base_weight_g = base_weight_g
        self.confidence = confidence
        self.color_bgr = color_bgr
        self.bbox = bbox  # (x, y, w, h)
        self.is_verified_produce = is_verified_produce


class ProduceDetector:
    """
    Real-time Fruit and Vegetable Object Identifier.
    Uses multi-space HSV color segmentation, fill-density profiling,
    morphological analysis, and geometric shape checks (circularity, aspect ratio, solidity)
    to classify authentic agricultural produce, reject foreign/unknown items,
    and estimate load-cell scale weight.
    """

    # Agricultural Produce Profiles with strict saturation & shape bounds
    PRODUCE_CATALOG = {
        "TOMATO": {
            "name": "Tomato (Grade-A)",
            "category": "Fresh Harvest / Solanaceae",
            "base_weight_g": 185.0,
            "weight_range": (120.0, 240.0),
            "hsv_ranges": [
                ((0, 110, 80), (10, 255, 255)),
                ((165, 110, 80), (180, 255, 255))
            ],
            "min_mean_sat": 95,
            "min_circularity": 0.52,
            "max_aspect_ratio": 1.40,
            "min_solidity": 0.72,
            "box_color": (0, 0, 230)  # Bright Red
        },
        "APPLE_RED": {
            "name": "Red Apple (Gala)",
            "category": "Pome Fruit / Orchard",
            "base_weight_g": 210.0,
            "weight_range": (150.0, 260.0),
            "hsv_ranges": [
                ((0, 120, 60), (10, 255, 230)),
                ((165, 120, 60), (180, 255, 230))
            ],
            "min_mean_sat": 100,
            "min_circularity": 0.55,
            "max_aspect_ratio": 1.35,
            "min_solidity": 0.75,
            "box_color": (30, 30, 200)
        },
        "APPLE_GREEN": {
            "name": "Green Apple (Granny Smith)",
            "category": "Pome Fruit / Orchard",
            "base_weight_g": 205.0,
            "weight_range": (150.0, 250.0),
            "hsv_ranges": [
                ((38, 95, 90), (75, 255, 255))
            ],
            "min_mean_sat": 90,
            "min_circularity": 0.55,
            "max_aspect_ratio": 1.35,
            "min_solidity": 0.75,
            "box_color": (50, 205, 50)
        },
        "BANANA": {
            "name": "Banana (Cavendish)",
            "category": "Tropical Harvest / Musaceae",
            "base_weight_g": 135.0,
            "weight_range": (100.0, 180.0),
            "hsv_ranges": [
                ((20, 120, 110), (36, 255, 255))
            ],
            "min_mean_sat": 110,
            "min_circularity": 0.12,
            "min_aspect_ratio": 1.7,  # Elongated
            "min_solidity": 0.60,
            "box_color": (0, 230, 255)  # Yellow
        },
        "CARROT": {
            "name": "Carrot (Organic)",
            "category": "Root Vegetable / Apiaceae",
            "base_weight_g": 95.0,
            "weight_range": (60.0, 140.0),
            "hsv_ranges": [
                ((10, 145, 100), (22, 255, 255))
            ],
            "min_mean_sat": 120,
            "min_circularity": 0.15,
            "min_aspect_ratio": 1.6,  # Tapered
            "min_solidity": 0.65,
            "box_color": (0, 140, 255)  # Orange
        },
        "GREENS": {
            "name": "Fresh Basil / Spinach",
            "category": "Leafy Herb / Sanitized",
            "base_weight_g": 55.0,
            "weight_range": (25.0, 90.0),
            "hsv_ranges": [
                ((35, 80, 45), (85, 255, 210))
            ],
            "min_mean_sat": 75,
            "min_circularity": 0.08,
            "min_solidity": 0.50,
            "box_color": (34, 139, 34)  # Forest Green
        },
        "POTATO": {
            "name": "Potato (Yukon Gold)",
            "category": "Tuber / Earth Harvest",
            "base_weight_g": 220.0,
            "weight_range": (140.0, 310.0),
            "hsv_ranges": [
                ((15, 65, 75), (26, 145, 185))
            ],
            "min_mean_sat": 60,
            "min_circularity": 0.42,
            "max_aspect_ratio": 1.7,
            "min_solidity": 0.70,
            "box_color": (92, 140, 175)  # Tan/Brown
        }
    }

    def __init__(self, roi_box: Optional[Tuple[int, int, int, int]] = None):
        """
        roi_box: Optional (x1, y1, x2, y2) defining scale weighing zone.
        Defaults to lower-left camera quadrant (x: 80-680, y: 180-640) for produce scanning.
        """
        # Default Inspection & Scale Platform Zone (x1, y1, x2, y2)
        self.roi = roi_box if roi_box else (60, 160, 680, 630)

        # Active detected item state
        self.current_item: Optional[ProduceItem] = None
        self.detection_history: List[str] = []
        self.simulated_item_override: Optional[ProduceItem] = None
        self.last_detection_time = 0.0

    def set_simulated_produce(self, produce_key: Optional[str]):
        """
        Allows interactive simulation of produce via keys (1-7 for produce, 8/u for foreign object, 0 to clear).
        Ensures testing without physical fruits/vegetables in front of the camera.
        """
        if produce_key is None or produce_key == "NONE" or produce_key == "0":
            self.simulated_item_override = None
            self.current_item = None
            return

        key_map = {
            "1": "TOMATO",
            "2": "APPLE_RED",
            "3": "BANANA",
            "4": "CARROT",
            "5": "GREENS",
            "6": "POTATO",
            "7": "APPLE_GREEN",
            "8": "UNKNOWN_OBJECT",
            "u": "UNKNOWN_OBJECT"
        }
        profile_key = key_map.get(str(produce_key).lower(), str(produce_key).upper())

        # Support foreign unknown item simulation
        if profile_key == "UNKNOWN_OBJECT":
            rx1, ry1, rx2, ry2 = self.roi
            cx, cy = (rx1 + rx2) // 2, (ry1 + ry2) // 2
            bw, bh = 150, 150
            bbox = (cx - bw // 2, cy - bh // 2, bw, bh)
            self.simulated_item_override = ProduceItem(
                name="Unknown Object (Unverified Item)",
                category="Foreign Item / Non-Produce",
                base_weight_g=235.0,
                confidence=0.35,
                color_bgr=(30, 140, 255),  # Warning Orange
                bbox=bbox,
                is_verified_produce=False
            )
            self.current_item = self.simulated_item_override
            return

        if profile_key in self.PRODUCE_CATALOG:
            p = self.PRODUCE_CATALOG[profile_key]
            # Bounding box placed centrally in inspection zone
            rx1, ry1, rx2, ry2 = self.roi
            cx, cy = (rx1 + rx2) // 2, (ry1 + ry2) // 2
            bw, bh = 180, 180
            bbox = (cx - bw // 2, cy - bh // 2, bw, bh)
            self.simulated_item_override = ProduceItem(
                name=p["name"],
                category=p["category"],
                base_weight_g=p["base_weight_g"],
                confidence=0.96,
                color_bgr=p["box_color"],
                bbox=bbox,
                is_verified_produce=True
            )
            self.current_item = self.simulated_item_override

    def detect_produce(self, frame_bgr: np.ndarray, hand_bboxes: Optional[List[Tuple[int, int, int, int]]] = None) -> Optional[ProduceItem]:
        """
        Scans the frame (focusing on the inspection ROI) to locate and classify produce.
        Applies strict color fill-density, mean saturation, and geometric profiling
        to reject unknown/foreign objects and human skin.
        """
        # If manual simulation active, return that
        if self.simulated_item_override:
            return self.simulated_item_override

        h, w = frame_bgr.shape[:2]
        rx1, ry1, rx2, ry2 = self.roi
        rx1, ry1 = max(0, rx1), max(0, ry1)
        rx2, ry2 = min(w, rx2), min(h, ry2)

        roi_frame = frame_bgr[ry1:ry2, rx1:rx2]
        if roi_frame.size == 0:
            return None

        # 1. Mask out user hands from ROI
        clean_roi = roi_frame.copy()
        if hand_bboxes:
            for hx, hy, hw, hh in hand_bboxes:
                hx1 = max(0, hx - rx1)
                hy1 = max(0, hy - ry1)
                hx2 = min(rx2 - rx1, hx + hw - rx1)
                hy2 = min(ry2 - ry1, hy + hh - ry1)
                if hx2 > hx1 and hy2 > hy1:
                    cv2.rectangle(clean_roi, (hx1, hy1), (hx2, hy2), (0, 0, 0), -1)

        # 2. Additional skin filter to prevent arms/fingers from matching produce
        ycrcb = cv2.cvtColor(clean_roi, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77], dtype=np.uint8),
                                       np.array([255, 173, 127], dtype=np.uint8))
        clean_roi[skin_mask > 0] = [0, 0, 0]

        hsv_roi = cv2.cvtColor(clean_roi, cv2.COLOR_BGR2HSV)
        hsv_roi = cv2.GaussianBlur(hsv_roi, (5, 5), 0)

        best_item: Optional[ProduceItem] = None
        highest_score = 0.0

        # 3. Match against verified agricultural produce catalog
        for key, profile in self.PRODUCE_CATALOG.items():
            combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
            for lower, upper in profile["hsv_ranges"]:
                lower_np = np.array(lower, dtype=np.uint8)
                upper_np = np.array(upper, dtype=np.uint8)
                mask = cv2.inRange(hsv_roi, lower_np, upper_np)
                combined_mask = cv2.bitwise_or(combined_mask, mask)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Ignore small camera noise (< 3200 pixels)
                if area < 3200 or area > 140000:
                    continue

                perimeter = cv2.arcLength(cnt, True)
                if perimeter <= 0:
                    continue

                circularity = (4 * math.pi * area) / (perimeter * perimeter)
                bx, by, bw, bh = cv2.boundingRect(cnt)
                aspect_ratio = float(max(bw, bh)) / max(1, min(bw, bh))

                # Shape geometry validation against produce profile
                shape_match = True
                if "min_circularity" in profile and circularity < profile["min_circularity"]:
                    shape_match = False
                if "max_aspect_ratio" in profile and aspect_ratio > profile["max_aspect_ratio"]:
                    shape_match = False
                if "min_aspect_ratio" in profile and aspect_ratio < profile["min_aspect_ratio"]:
                    shape_match = False

                if not shape_match:
                    continue

                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = float(area) / max(1, hull_area)
                min_sol = profile.get("min_solidity", 0.65)
                if solidity < min_sol:
                    continue

                # Bounding-box fill ratio: real produce fills substantial portion of bounding box
                fill_ratio = float(area) / max(1.0, bw * bh)
                if fill_ratio < 0.35:
                    continue

                # Mean saturation inside contour to reject muted desk/background objects
                cnt_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                mean_val = cv2.mean(hsv_roi, mask=cnt_mask)
                mean_sat = mean_val[1]
                if mean_sat < profile.get("min_mean_sat", 80):
                    continue

                score = (area / 45000.0) * 0.4 + (solidity * 0.3) + (min(1.0, circularity) * 0.3)
                if score > highest_score:
                    highest_score = score
                    area_factor = math.sqrt(area / 18000.0)
                    min_w, max_w = profile["weight_range"]
                    est_weight = np.clip(profile["base_weight_g"] * area_factor, min_w, max_w)

                    best_item = ProduceItem(
                        name=profile["name"],
                        category=profile["category"],
                        base_weight_g=float(round(est_weight, 1)),
                        confidence=min(0.97, 0.78 + score * 0.2),
                        color_bgr=profile["box_color"],
                        bbox=(rx1 + bx, ry1 + by, bw, bh),
                        is_verified_produce=True
                    )

        # 4. Check for Foreign / Unknown Objects in Weighing Zone
        # If no verified agricultural produce matched, check if an unverified physical object is present
        if best_item is None:
            gray_roi = cv2.cvtColor(clean_roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray_roi, (7, 7), 0)
            edges = cv2.Canny(blurred, 35, 110)
            e_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            edges = cv2.dilate(edges, e_kernel, iterations=2)
            edge_cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for ec in edge_cnts:
                e_area = cv2.contourArea(ec)
                if e_area >= 4000 and e_area <= 130000:
                    ebx, eby, ebw, ebh = cv2.boundingRect(ec)
                    if ebw >= 50 and ebh >= 50:
                        est_weight = float(round(np.clip(e_area / 75.0, 60.0, 500.0), 1))
                        best_item = ProduceItem(
                            name="Unknown Object (Unverified Item)",
                            category="Foreign Item / Non-Produce",
                            base_weight_g=est_weight,
                            confidence=0.35,
                            color_bgr=(30, 140, 255),  # Amber warning color
                            bbox=(rx1 + ebx, ry1 + eby, ebw, ebh),
                            is_verified_produce=False
                        )
                        break

        self.current_item = best_item
        return best_item

    def draw_inspection_zone(self, frame: np.ndarray, detected_item: Optional[ProduceItem] = None) -> None:
        """
        Draws the Produce Scanning & Weighing Platform zone on the HUD.
        Renders green status for verified produce and prominent amber warning for foreign items.
        """
        rx1, ry1, rx2, ry2 = self.roi

        # Determine zone state & bracket color
        if detected_item:
            if detected_item.is_verified_produce:
                bracket_color = (0, 220, 180)  # Emerald Green
                tag_text = f"PRODUCE VERIFIED: {detected_item.name.upper()}"
            else:
                bracket_color = (30, 140, 255)  # Amber Warning
                tag_text = "WARNING: FOREIGN / UNVERIFIED OBJECT ON SCALE"
        else:
            bracket_color = (140, 140, 140)  # Neutral Gray
            tag_text = "SCALE WEIGHING PLATFORM (EMPTY)"

        thick = 2
        cv2.putText(frame, tag_text, (rx1 + 10, ry1 - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, bracket_color, 1, cv2.LINE_AA)

        # Draw Corner Brackets
        corner_len = 35
        # Top-Left
        cv2.line(frame, (rx1, ry1), (rx1 + corner_len, ry1), bracket_color, thick)
        cv2.line(frame, (rx1, ry1), (rx1, ry1 + corner_len), bracket_color, thick)
        # Top-Right
        cv2.line(frame, (rx2, ry1), (rx2 - corner_len, ry1), bracket_color, thick)
        cv2.line(frame, (rx2, ry1), (rx2, ry1 + corner_len), bracket_color, thick)
        # Bottom-Left
        cv2.line(frame, (rx1, ry2), (rx1 + corner_len, ry2), bracket_color, thick)
        cv2.line(frame, (rx1, ry2), (rx1, ry2 - corner_len), bracket_color, thick)
        # Bottom-Right
        cv2.line(frame, (rx2, ry2), (rx2 - corner_len, ry2), bracket_color, thick)
        cv2.line(frame, (rx2, ry2), (rx2, ry2 - corner_len), bracket_color, thick)

        # Highlight detected item bounding box & status pill
        if detected_item and detected_item.bbox:
            bx, by, bw, bh = detected_item.bbox
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), detected_item.color_bgr, 2)
            if detected_item.is_verified_produce:
                label = f"{detected_item.name} ({int(detected_item.confidence * 100)}%)"
            else:
                label = "REJECTED: UNKNOWN OBJECT (NON-PRODUCE)"

            cv2.rectangle(frame, (bx, by - 24), (bx + len(label) * 11, by), detected_item.color_bgr, -1)
            cv2.putText(frame, label, (bx + 4, by - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
