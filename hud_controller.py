"""
hud_controller.py
AgriTouchless: Farm & Kitchen Hygiene Controller
Member 2: Application State, UI/HUD & Audio Lead
"""

import time
import random
import cv2
import numpy as np

try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


def _generate_tone(frequency=440, duration=0.1, sample_rate=22050):
    """Generates a simple sine wave pygame Sound."""
    if not PYGAME_AVAILABLE:
        return None
    try:
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.4 * np.sin(2 * np.pi * frequency * t)
        sound_array = (wave * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(sound_array)
        return sound
    except Exception:
        return None


class HUDController:
    """
    Manages application state (Digital Scale, SOP Steps, Emergency Stop)
    and renders the OpenCV Heads-Up Display (HUD) overlay at 1280x720.
    """

    # Palette (BGR)
    COLOR_SAFE = (120, 200, 80)       # Emerald Green
    COLOR_PROGRESS = (0, 191, 255)    # Amber Yellow
    COLOR_ALERT = (60, 20, 220)       # Crimson Red
    COLOR_PANEL_BG = (30, 30, 30)     # Semi-transparent Charcoal
    COLOR_WHITE = (240, 240, 240)
    COLOR_GRAY = (160, 160, 160)
    COLOR_ACCENT = (255, 165, 0)      # Cyan / Sky Accent

    def __init__(self):
        # Digital Scale state with dynamic load-cell simulation
        self.raw_weight = 0.0       # Gross load-cell weight
        self.target_weight = 0.0    # Target weight of placed produce
        self.tare_offset = 0.0      # Stored tare baseline
        self.is_tared = False
        self.last_weight_update = time.time()
        self.detected_produce_name = "EMPTY PLATTER"
        self.detected_produce_category = "Awaiting Produce in Zone"

        # SOP / Recipe state
        self.steps = [
            "1. Sanitize workstation & inspect scale calibration.",
            "2. Wash & sort Grade-A tomatoes into sanitized crate #2.",
            "3. Weigh 500g fresh produce & portion into clean bins.",
            "4. Pack sorted vegetables into eco-crates for shipping.",
            "5. Seal crates, record batch ID & wipe scale platform."
        ]
        self.current_step_idx = 1  # Start at step 2/5 as per design spec
        self.step_start_time = time.time()

        # Emergency Stop state
        self.emergency_stop = False
        self.e_stop_flash_state = False
        self.last_flash_time = time.time()

        # Performance & Stats
        self.fps = 30.0

        # Audio synthesizer
        self.sound_tare = _generate_tone(frequency=880, duration=0.15)
        self.sound_step = _generate_tone(frequency=587, duration=0.1)
        self.sound_alert = _generate_tone(frequency=260, duration=0.35)

    def play_sound(self, sound_type: str):
        """Play low-latency feedback sound."""
        if not PYGAME_AVAILABLE:
            return
        try:
            if sound_type == "tare" and self.sound_tare:
                self.sound_tare.play()
            elif sound_type == "step" and self.sound_step:
                self.sound_step.play()
            elif sound_type == "alert" and self.sound_alert:
                self.sound_alert.play()
        except Exception:
            pass

    def tare_scale(self):
        """Zero out the digital scale with current load as tare offset."""
        self.tare_offset = self.raw_weight
        self.is_tared = True
        self.play_sound("tare")

    def next_step(self):
        """Advance to next SOP / Recipe step."""
        if self.current_step_idx < len(self.steps) - 1:
            self.current_step_idx += 1
            self.step_start_time = time.time()
            self.play_sound("step")

    def prev_step(self):
        """Return to previous SOP / Recipe step."""
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self.step_start_time = time.time()
            self.play_sound("step")

    def toggle_emergency_stop(self):
        """Toggle emergency stop fail-safe state."""
        self.emergency_stop = not self.emergency_stop
        self.play_sound("alert")

    def update_simulation(self, detected_produce=None):
        """
        Simulate realistic load-cell settling physics and micro-sensor noise.
        """
        if detected_produce:
            self.target_weight = detected_produce.base_weight_g
            self.detected_produce_name = detected_produce.name
            self.detected_produce_category = detected_produce.category
        else:
            self.target_weight = 0.0
            self.detected_produce_name = "EMPTY PLATTER"
            self.detected_produce_category = "Awaiting Produce in Zone"

        if not self.emergency_stop:
            diff = self.target_weight - self.raw_weight
            self.raw_weight += diff * 0.28
            # Micro-fluctuation (+/- 0.15g)
            noise = random.uniform(-0.15, 0.15) if abs(self.raw_weight) > 1.0 else random.uniform(-0.04, 0.04)
            self.raw_weight += noise

    @property
    def net_weight(self) -> float:
        val = self.raw_weight - self.tare_offset
        if abs(val) < 0.2:
            return 0.0
        return val

    def draw_circular_progress(self, frame: np.ndarray, center: tuple, progress: float):
        """
        Draws circular dwell-time progress indicator around wrist/palm (0.0 to 1.0).
        """
        if progress <= 0.0 or center is None:
            return

        cx, cy = int(center[0]), int(center[1])
        radius = 45
        axes = (radius, radius)

        # Background track
        cv2.circle(frame, (cx, cy), radius, (80, 80, 80), 3, cv2.LINE_AA)

        # Progress arc
        angle = int(360 * min(1.0, progress))
        if angle > 0:
            cv2.ellipse(frame, (cx, cy), axes, -90, 0, angle, self.COLOR_PROGRESS, 5, cv2.LINE_AA)

    def render(self, frame: np.ndarray, hands_detected: int = 0,
               current_gesture: str = "NONE", dwell_progress: float = 0.0,
               dwell_center: tuple = None, detected_produce=None) -> np.ndarray:
        """
        Renders the complete HUD overlay on top of the webcam frame.
        Target resolution: 1280x720.
        """
        h, w = frame.shape[:2]
        if w != 1280 or h != 720:
            frame = cv2.resize(frame, (1280, 720))
            h, w = 720, 1280

        self.update_simulation(detected_produce)

        overlay = frame.copy()

        # 1. Top Status Bar (y: 0 to 50)
        cv2.rectangle(overlay, (0, 0), (w, 50), self.COLOR_PANEL_BG, -1)

        # 2. Digital Scale Card (x: 760 to 1250, y: 65 to 245)
        cv2.rectangle(overlay, (760, 65), (1250, 245), self.COLOR_PANEL_BG, -1)

        # 3. SOP / Recipe Step Card (x: 760 to 1250, y: 260 to 520)
        cv2.rectangle(overlay, (760, 260), (1250, 520), self.COLOR_PANEL_BG, -1)

        # 4. Bottom Emergency Banner (y: 660 to 710)
        cv2.rectangle(overlay, (0, 660), (w, 710), self.COLOR_PANEL_BG, -1)

        # Blend semi-transparent panels (alpha = 0.65)
        alpha = 0.65
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Panel Borders & Dividers
        cv2.rectangle(frame, (760, 65), (1250, 245), (70, 70, 70), 2)
        cv2.rectangle(frame, (760, 260), (1250, 520), (70, 70, 70), 2)
        cv2.line(frame, (0, 50), (w, 50), (90, 90, 90), 2)
        cv2.line(frame, (0, 660), (w, 660), (90, 90, 90), 2)

        # --- Top Status Bar Text ---
        status_text = "SYSTEM: EMERGENCY STOP" if self.emergency_stop else "SYSTEM: RUNNING"
        status_color = self.COLOR_ALERT if self.emergency_stop else self.COLOR_SAFE
        cv2.putText(frame, status_text, (25, 33), cv2.FONT_HERSHEY_DUPLEX, 0.75, status_color, 2, cv2.LINE_AA)

        fps_text = f"FPS: {int(self.fps)}"
        cv2.putText(frame, fps_text, (520, 33), cv2.FONT_HERSHEY_DUPLEX, 0.65, self.COLOR_WHITE, 1, cv2.LINE_AA)

        hands_text = f"HANDS: {hands_detected}/2"
        cv2.putText(frame, hands_text, (720, 33), cv2.FONT_HERSHEY_DUPLEX, 0.65, self.COLOR_WHITE, 1, cv2.LINE_AA)

        gesture_text = f"GESTURE: {current_gesture}"
        cv2.putText(frame, gesture_text, (940, 33), cv2.FONT_HERSHEY_DUPLEX, 0.65, self.COLOR_PROGRESS, 2, cv2.LINE_AA)

        # --- Digital Scale Simulator Card ---
        cv2.putText(frame, "DIGITAL SCALE SIMULATOR", (780, 95),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, self.COLOR_WHITE, 2, cv2.LINE_AA)

        # Display detected produce name & status tag
        cv2.putText(frame, f"Item: {self.detected_produce_name}", (780, 125),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 230, 255), 1, cv2.LINE_AA)

        net_w = self.net_weight
        weight_str = f"{net_w:+,.1f} g" if abs(net_w) > 0.0 else "0.0 g"

        # Badge decision
        if abs(net_w) < 0.3:
            badge_text = "[TARED / ZEROED]" if self.is_tared else "[EMPTY PLATTER]"
            badge_color = self.COLOR_SAFE
            w_color = self.COLOR_SAFE
        elif net_w > 0.3:
            badge_text = "[NET READING]"
            badge_color = self.COLOR_PROGRESS
            w_color = self.COLOR_PROGRESS
        else:
            badge_text = "[ITEM REMOVED]"
            badge_color = (120, 120, 255)
            w_color = (120, 120, 255)

        cv2.putText(frame, f"Weight: {weight_str}", (780, 168),
                    cv2.FONT_HERSHEY_DUPLEX, 1.05, w_color, 2, cv2.LINE_AA)
        cv2.putText(frame, badge_text, (1080, 168),
                    cv2.FONT_HERSHEY_DUPLEX, 0.50, badge_color, 1, cv2.LINE_AA)

        # Gross & Tare readout
        gross_info = f"Gross: {self.raw_weight:,.1f} g  |  Tare: {self.tare_offset:,.1f} g"
        cv2.putText(frame, gross_info, (780, 202),
                    cv2.FONT_HERSHEY_DUPLEX, 0.48, self.COLOR_GRAY, 1, cv2.LINE_AA)

        tare_note = "[Hold Fist 1s: Tare | Keys 1-6: Place Fruit/Veg | 0: Clear]"
        cv2.putText(frame, tare_note, (780, 230),
                    cv2.FONT_HERSHEY_DUPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

        # --- Active SOP / Recipe Card ---
        step_title = f"ACTIVE SOP / RECIPE STEP ({self.current_step_idx + 1}/{len(self.steps)})"
        cv2.putText(frame, step_title, (780, 295),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, self.COLOR_WHITE, 2, cv2.LINE_AA)

        step_elapsed = int(time.time() - self.step_start_time)
        mins, secs = divmod(step_elapsed, 60)
        cv2.putText(frame, f"Elapsed: {mins:02d}:{secs:02d}", (780, 335),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, self.COLOR_PROGRESS, 1, cv2.LINE_AA)

        # Step description (wrapped)
        step_desc = self.steps[self.current_step_idx]
        words = step_desc.split(" ")
        line1, line2 = "", ""
        for word in words:
            if len(line1 + " " + word) < 32:
                line1 += (" " if line1 else "") + word
            else:
                line2 += (" " if line2 else "") + word

        cv2.putText(frame, line1, (780, 385),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, self.COLOR_WHITE, 1, cv2.LINE_AA)
        if line2:
            cv2.putText(frame, line2, (780, 420),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, self.COLOR_WHITE, 1, cv2.LINE_AA)

        cv2.putText(frame, "[<< Swipe Left | Swipe Right >>]", (780, 485),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, self.COLOR_PROGRESS, 1, cv2.LINE_AA)

        # --- Emergency Banner ---
        banner_text = "[EMERGENCY BANNER] Raise BOTH Open Palms to Trigger EMERGENCY STOP"
        cv2.putText(frame, banner_text, (200, 693),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, (100, 100, 255), 2, cv2.LINE_AA)

        # --- Dwell Time Circular Progress ---
        if dwell_progress > 0.0 and dwell_center is not None:
            self.draw_circular_progress(frame, dwell_center, dwell_progress)

        # --- Emergency Stop Full-Screen Flash Overlay ---
        if self.emergency_stop:
            now = time.time()
            if now - self.last_flash_time > 0.5:
                self.e_stop_flash_state = not self.e_stop_flash_state
                self.last_flash_time = now

            if self.e_stop_flash_state:
                red_alert = frame.copy()
                cv2.rectangle(red_alert, (0, 0), (w, h), self.COLOR_ALERT, -1)
                cv2.addWeighted(red_alert, 0.35, frame, 0.65, 0, frame)

            alert_box_y = int(h / 2)
            cv2.rectangle(frame, (100, alert_box_y - 60), (w - 100, alert_box_y + 60), (20, 20, 160), -1)
            cv2.rectangle(frame, (100, alert_box_y - 60), (w - 100, alert_box_y + 60), self.COLOR_ALERT, 3)
            cv2.putText(frame, "EMERGENCY STOP ACTIVATED", (w // 2 - 380, alert_box_y),
                        cv2.FONT_HERSHEY_DUPLEX, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
            cv2.putText(frame, "Raise BOTH Open Palms again to Resume System", (w // 2 - 320, alert_box_y + 40),
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, self.COLOR_WHITE, 1, cv2.LINE_AA)

        return frame
