import streamlit as st
import json
import os
import requests
import base64
import assist

import time
import logging
from gpiozero import OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory

# Add import for MOTORS
from controller import MOTORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pins for Pump 1 (adjust if needed)
IA = 17
IB = 4

# Use LGPIOFactory for RPi5 compatibility
factory = LGPIOFactory()

# Initialize devices and test sequentially
devices = []
try:
    for pump_num, (ia, ib) in enumerate(MOTORS, 1):
        logger.info(f'Testing Pump {pump_num} with pins {ia} and {ib}')
        
        dev_a = OutputDevice(ia, pin_factory=factory, active_high=True, initial_value=False)
        dev_b = OutputDevice(ib, pin_factory=factory, active_high=True, initial_value=False)
        devices.extend([dev_a, dev_b])
        
        # Test forward (non-inverted)
        logger.info(f'Forward (non-inverted): Setting {ia} HIGH, {ib} LOW')
        dev_a.on()
        dev_b.off()
        time.sleep(2)
        
        # Stop
        logger.info(f'Stop: Setting both LOW')
        dev_a.off()
        dev_b.off()
        time.sleep(2)
        
        # Test reverse (non-inverted)
        logger.info(f'Reverse (non-inverted): Setting {ia} LOW, {ib} HIGH')
        dev_a.off()
        dev_b.on()
        time.sleep(2)
        
        # Stop
        logger.info(f'Stop: Setting both LOW')
        dev_a.off()
        dev_b.off()
        time.sleep(2)
        
        # Test inverted forward
        logger.info(f'Forward (inverted): Setting {ia} LOW, {ib} HIGH')
        dev_a.off()
        dev_b.on()
        time.sleep(2)
        
        # Stop and pause before next pump
        dev_a.off()
        dev_b.off()
        time.sleep(5)
        
except KeyboardInterrupt:
    logger.info('Test stopped.')
finally:
    for dev in devices:
        dev.close()


# ---------- Global Setup ----------
CONFIG_FILE = "pump_config.json"
COCKTAILS_FILE = "cocktails.json"
LOGO_FOLDER = "drink_logos"

# Ensure logo folder exists.
if not os.path.exists(LOGO_FOLDER):
    os.makedirs(LOGO_FOLDER)

# Initialize session state for selected cocktail.
if "selected_cocktail" not in st.session_state:
    st.session_state.selected_cocktail = None

# ---------- Helper Functions ----------
def load_saved_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
    return {}

def load_cocktails():
    if os.path.exists(COCKTAILS_FILE):
        try:
            with open(COCKTAILS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading cocktails: {e}")
    return {}

def save_cocktails(data):
    try:
        with open(COCKTAILS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving cocktails: {e}")

def get_safe_name(name):
    return name.lower().replace(" ", "_")

def select_cocktail(safe_name):
    st.session_state.selected_cocktail = safe_name

def clear_selected():
    st.session_state.selected_cocktail = None

# ---------- Main App: Two Tabs (Settings and Recipe Book) ----------
tabs = st.tabs(["Settings", "Recipe Book"])

# ------------------ Settings Tab ------------------
with tabs[0]:
    st.markdown("<h1 style='text-align: center;'>Cocktail Recipe Generator - Settings</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Enter the drink names for each pump:</p>", unsafe_allow_html=True)

    saved_config = load_saved_config()
    pump_inputs = {}

    col1, col2 = st.columns(2)
    def get_default(pump_name):
        if pump_name in saved_config:
            return saved_config[pump_name]
        elif pump_name == "Pump 1":
            return "vodka"
        else:
            return ""

    with col1:
        for i in range(1, 6):
            pump_name = f"Pump {i}"
            pump_inputs[pump_name] = st.text_input(pump_name, value=get_default(pump_name), label_visibility="collapsed")
    with col2:
        for i in range(6, 11):
            pump_name = f"Pump {i}"
            pump_inputs[pump_name] = st.text_input(pump_name, value=get_default(pump_name), label_visibility="collapsed")

    # New section for bartender requests.
    st.markdown("<h3 style='text-align: center;'>Requests for the bartender</h3>", unsafe_allow_html=True)
    bartender_requests = st.text_area("Enter any special requests for the bartender", height=100)

    if st.button("Generate Recipes"):
        pump_to_drink = {pump: drink for pump, drink in pump_inputs.items() if drink.strip()}
        # Save pump configuration.
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(pump_to_drink, f, indent=2)
        except Exception as e:
            st.error(f"Error saving configuration: {e}")
        st.markdown(f"<p style='text-align: center;'>Pump configuration: {pump_to_drink}</p>", unsafe_allow_html=True)

        cocktails_json = assist.generate_cocktails(pump_to_drink, bartender_requests)
        try:
            with open(COCKTAILS_FILE, "w") as f:
                json.dump(cocktails_json, f, indent=2)
            st.success("Cocktails JSON saved to cocktails.json")
        except Exception as e:
            st.error(f"Error saving cocktails: {e}")

        # --- Generate and Cache Images with Progress Bar ---
        st.markdown("<h2 style='text-align: center;'>Generating Cocktail Logos...</h2>", unsafe_allow_html=True)
        image_paths = {}
        cocktails = cocktails_json.get("cocktails", [])
        progress_bar = st.progress(0, text="Generating images...")
        total = len(cocktails) if cocktails else 1
        for idx, cocktail in enumerate(cocktails):
            normal_name = cocktail.get("normal_name", "unknown_drink")
            safe_name = get_safe_name(normal_name)
            filename = os.path.join(LOGO_FOLDER, f"{safe_name}.png")
            if os.path.exists(filename):
                image_paths[normal_name] = filename
            else:
                prompt = (
                    f"A realistic illustration of a {normal_name} cocktail on a plain white background. "
                    "The lighting and shading create depth and realism, making the drink appear fresh and inviting."
                )
                try:
                    image_url = assist.generate_image(prompt)
                    img_data = requests.get(image_url).content
                    with open(filename, "wb") as f:
                        f.write(img_data)
                    image_paths[normal_name] = filename
                except Exception as e:
                    image_paths[normal_name] = f"Error: {e}"
            progress_bar.progress((idx + 1) / total)
        progress_bar.empty()
        st.success("Image generation complete.")

# ------------------ Recipe Book Tab ------------------
with tabs[1]:
    st.markdown("<h1 style='text-align: center;'>Recipe Book</h1>", unsafe_allow_html=True)
    cocktail_data = load_cocktails()

    # If a cocktail has been selected, display its detail view.
    if st.session_state.selected_cocktail:
        safe_name = st.session_state.selected_cocktail
        selected_cocktail = None
        for cocktail in cocktail_data.get("cocktails", []):
            if get_safe_name(cocktail.get("normal_name", "")) == safe_name:
                selected_cocktail = cocktail
                break
        if selected_cocktail is None:
            st.error("Cocktail not found.")
        else:
            st.markdown(f"<h1 style='text-align: center;'>{selected_cocktail.get('fun_name', 'Cocktail')}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{selected_cocktail.get('normal_name', '')}</h3>", unsafe_allow_html=True)
            image_file = os.path.join(LOGO_FOLDER, f"{safe_name}.png")
            if os.path.exists(image_file):
                st.image(image_file, use_container_width=True)
            else:
                st.write("Image not found.")
            st.markdown("<h2 style='text-align: center;'>Recipe</h2>", unsafe_allow_html=True)
            recipe_adjustments = {}
            for ingredient, measurement in selected_cocktail.get("ingredients", {}).items():
                parts = measurement.split()
                try:
                    default_value = float(parts[0])
                    unit = " ".join(parts[1:]) if len(parts) > 1 else ""
                except:
                    default_value = 1.0
                    unit = measurement
                value = st.slider(
                    f"{ingredient} ({measurement})",
                    min_value=0.0,
                    max_value=default_value * 4,
                    value=default_value,
                    step=0.1,
                )
                recipe_adjustments[ingredient] = f"{value} {unit}".strip()
            st.markdown("<h3 style='text-align: center;'><strong>Adjusted Recipe</strong></h3>", unsafe_allow_html=True)
            st.json(recipe_adjustments)
            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("Save Recipe"):
                    updated = False
                    for idx, cocktail in enumerate(cocktail_data.get("cocktails", [])):
                        if get_safe_name(cocktail.get("normal_name", "")) == safe_name:
                            cocktail_data["cocktails"][idx]["ingredients"] = recipe_adjustments
                            updated = True
                            break
                    if updated:
                        save_cocktails(cocktail_data)
                        st.success("Recipe saved!")
                    else:
                        st.error("Failed to update recipe.")
            with cols[1]:
                if st.button("Pour"):
                    st.info("Pouring... (dummy action)")
            if st.button("Back to Gallery"):
                clear_selected()
    else:
        # Display gallery of cocktails.
        image_paths = {}
        if os.path.exists(COCKTAILS_FILE):
            cocktail_data = load_cocktails()
            for cocktail in cocktail_data.get("cocktails", []):
                normal_name = cocktail.get("normal_name", "unknown_drink")
                safe_name = get_safe_name(normal_name)
                filename = os.path.join(LOGO_FOLDER, f"{safe_name}.png")
                if os.path.exists(filename):
                    image_paths[normal_name] = filename
            if image_paths:
                for cocktail_name, path in image_paths.items():
                    safe_name = get_safe_name(cocktail_name)
                    with st.container():
                        st.markdown(f"<h3 style='text-align: center;'>{cocktail_name}</h3>", unsafe_allow_html=True)
                        with open(path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                        st.markdown(
                            f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded_string}' width='300'></div>",
                            unsafe_allow_html=True,
                        )
                        btn_cols = st.columns([2, 1, 1, 2])
                        with btn_cols[1]:
                            if st.button("View", key=f"view_{safe_name}", on_click=select_cocktail, args=(safe_name,)):
                                pass
                        with btn_cols[2]:
                            if st.button("Pour", key=f"pour_{safe_name}"):
                                st.info("Pouring... (dummy action)")
            else:
                st.markdown("<p style='text-align: center;'>No cocktail images found.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center;'>No recipes generated yet. Please use the Settings tab to generate recipes.</p>", unsafe_allow_html=True)
