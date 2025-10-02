# interface.py
import pygame
import json
import qrcode
import io
import socket
import os

from settings import *
from helpers import get_cocktail_image_path, get_valid_cocktails, wrap_text, favorite_cocktail, unfavorite_cocktail, get_centered_rect_for_surface
from controller import make_drink

import logging
logger = logging.getLogger(__name__)

# Grabs the local IP address of the device for the Streamlit app access
def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def create_qr_code_slide():
    """Create a QR code slide for the Streamlit app access"""
    # Get local IP and port
    local_ip = get_local_ip()
    streamlit_port = 8501
    url = f"http://{local_ip}:{streamlit_port}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to pygame surface
    img_buffer = io.BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Load into pygame
    qr_surface = pygame.image.load(img_buffer)
    
    # Scale to fit screen (make it large enough to scan easily)
    qr_size = min(screen_width, screen_height) // 2
    qr_surface = pygame.transform.scale(qr_surface, (qr_size, qr_size))
    
    # Create a cocktail-like object for the QR code slide
    qr_cocktail = {
        'normal_name': 'Access App',
        'fun_name': 'Scan QR Code',
        'qr_surface': qr_surface,
        'url': url,
        'is_qr_slide': True
    }
    
    return qr_cocktail

def get_cocktails_with_qr():
    """Get valid cocktails and add QR code slide at the end"""
    cocktails = get_valid_cocktails()
    qr_cocktail = create_qr_code_slide()
    cocktails.append(qr_cocktail)
    return cocktails

def check_for_refresh_signal():
    """Check if there's a signal from the app to refresh cocktails"""
    try:
        if os.path.exists('interface_signal.json'):
            with open('interface_signal.json', 'r') as f:
                signal = json.load(f)
            
            # Check if it's a refresh signal
            if signal.get('action') == 'refresh_cocktails':
                # Remove the signal file after reading
                os.remove('interface_signal.json')
                logger.info("Received refresh signal from app")
                return True
    except Exception as e:
        logger.error(f"Error checking refresh signal: {e}")
    
    return False

pygame.init()
if FULL_SCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
screen_size = screen.get_size()
screen_width, screen_height = screen_size
cocktail_image_offset = screen_width * (1.0 - COCKTAIL_IMAGE_SCALE) // 2
pygame.display.set_caption('Cocktail Swipe')

normal_text_size = 72
small_text_size = int(normal_text_size * 0.6)
text_position = (screen_width // 2, int(screen_height * 0.85))

def add_layer(*args, function=screen.blit, key=None):
    if key == None:
        key = len(layers)
    layers[str(key)] = {'function': function, 'args': args}

def remove_layer(key):
    try:
        del layers[key]
    except KeyError:
        pass
    
layers = {}
def draw_frame():
    for layer in layers.values():
        layer['function'](*layer['args'])
    pygame.display.flip()

def animate_logo_click(logo, rect, base_size, target_size, layer_key, duration=150):
    """Animate a logo click (pop effect): grow from base_size to target_size then shrink back."""
    clock = pygame.time.Clock()
    center = rect.center
    # Expand
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        current_size = int(base_size + (target_size - base_size) * progress)
        scaled_img = pygame.transform.scale(logo, (current_size, current_size))
        new_rect = scaled_img.get_rect(center=center)
        add_layer(scaled_img, new_rect, key=layer_key)
        draw_frame()
        if progress >= 1.0:
            break
        clock.tick(60)
    # Shrink back
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        current_size = int(target_size - (target_size - base_size) * progress)
        scaled_img = pygame.transform.scale(logo, (current_size, current_size))
        new_rect = scaled_img.get_rect(center=center)
        add_layer(scaled_img, new_rect, key=layer_key)
        draw_frame()
        if progress >= 1.0:
            break
        clock.tick(60)

def animate_logo_rotate(logo, rect, layer_key, rotation=180):
    """Animate a logo click (rotate effect): rotate the amount of rotation provided"""
    angle = 0
    while angle < rotation:
        angle = (angle + 5) % 360
        rotated_loading = pygame.transform.rotate(logo, angle * -1)
        rotated_rect = rotated_loading.get_rect(center=rect.center)
        # Draw loading image first (under)
        add_layer(rotated_loading, rotated_rect, key=layer_key)
        draw_frame()

def animate_both_logos_zoom(single_logo, double_logo, single_rect, double_rect, base_size, target_size, duration=300):
    """Animate both logos zooming in together and then shrinking back."""
    clock = pygame.time.Clock()
    center_single = single_rect.center
    center_double = double_rect.center
    # Expand
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        current_size = int(base_size + (target_size - base_size) * progress)
        scaled_single = pygame.transform.scale(single_logo, (current_size, current_size))
        scaled_double = pygame.transform.scale(double_logo, (current_size, current_size))
        new_rect_single = scaled_single.get_rect(center=center_single)
        new_rect_double = scaled_double.get_rect(center=center_double)
        add_layer(scaled_single, new_rect_single, key='single_logo')
        add_layer(scaled_double, new_rect_double, key='double_logo')
        draw_frame()
        if progress >= 1.0:
            break
        clock.tick(60)
    # Contract
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        current_size = int(target_size - (target_size - base_size) * progress)
        scaled_single = pygame.transform.scale(single_logo, (current_size, current_size))
        scaled_double = pygame.transform.scale(double_logo, (current_size, current_size))
        new_rect_single = scaled_single.get_rect(center=center_single)
        new_rect_double = scaled_double.get_rect(center=center_double)
        add_layer(scaled_single, new_rect_single, key='single_logo')
        add_layer(scaled_double, new_rect_double, key='double_logo')
        draw_frame()
        if progress >= 1.0:
            break
        clock.tick(60)

def show_pouring_and_loading(watcher):
    """Overlay pouring_img full screen and a spinning loading_img (720x720) drawn underneath."""
    try:
        pouring_img = pygame.image.load('nav-photos/pouring.png')
        pouring_img = pygame.transform.scale(pouring_img, screen_size)
    except Exception as e:
        logger.exception('Error loading nav-photos/pouring.png')
        pouring_img = None
    try:
        loading_img = pygame.image.load('nav-photos/loading.png')
        loading_img = pygame.transform.scale(loading_img, (70, 70))
    except Exception as e:
        logger.exception('Error loading nav-photos/loading.png')
        loading_img = None
    try:
        checkmark_img = pygame.image.load('nav-photos/checkmark.png')
        checkmark_img = pygame.transform.scale(checkmark_img, (30, 30))
    except Exception as e:
        logger.exception('Error loading nav-photos/checkmark.png')
        checkmark_img = None
        
    angle = 0

    # Add a background layer
    add_layer(*layers['background']['args'], function=layers['background']['function'], key='pouring_background')
    # Then draw pouring image on top
    if pouring_img:
        add_layer(pouring_img, (0, -150), key='pouring')

    pour_layers = []
    pouring_line = 0
    while not watcher.done():
        angle = (angle - 5) % 360
        if loading_img:
            rotated_loading = pygame.transform.rotate(loading_img, angle)
        
        for index, pour in enumerate(watcher.pours):
            layer_key = f'pour_{index}'
            logo_layer_key = f'{layer_key}_logo'
            
            x_position = screen_width // 3
            y_position = (text_position[1] + small_text_size * pouring_line) - 325

            if logo_layer_key not in pour_layers:
                font = pygame.font.SysFont(None, small_text_size)
                for layer_index, line in enumerate(wrap_text(str(pour), font, screen_width * 0.5)):
                    line_key = f'{layer_key}_{layer_index}'
                    text_surface = font.render(line, True, (255, 255, 255))
                    line_y_position = y_position + small_text_size * layer_index
                    if layer_index > 0:
                        line_y_position = line_y_position - 10 * layer_index
                    text_rect = text_surface.get_rect(topleft=(x_position, line_y_position))
                    pour_layers.append(line_key)
                    add_layer(text_surface, text_rect, key=line_key)
                    pouring_line += 1
                pour_layers.append(logo_layer_key)

            status_position = layers.get(logo_layer_key, {}).get('args', [None, None])[1]
            if status_position:
                status_position = status_position.center
            else:
                status_position = (x_position - small_text_size // 2, y_position - 7 + small_text_size // 2)

            if pour.running and loading_img:
                rect = rotated_loading.get_rect(center=status_position)
                add_layer(rotated_loading, rect, key=logo_layer_key)
            else:
                if checkmark_img:
                    rect = checkmark_img.get_rect(center=status_position)
                    add_layer(checkmark_img, rect, key=logo_layer_key)
                else:
                    remove_layer(logo_layer_key)
                    

        draw_frame()

    for layer in pour_layers:
        remove_layer(layer)

    remove_layer('pouring')
    remove_layer('pouring_background')
    draw_frame()
    pygame.event.clear()  # Drop all events that happened while pouring

def show_top_off_screen(manual_ingredients, cocktail_name, timeout=30000):
    """Display a screen instructing to top off with manual ingredients."""
    overlay = pygame.Surface(screen_size)
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    add_layer(overlay, (0, 0), key='top_off_overlay')

    font = pygame.font.SysFont(None, 60)
    title = font.render(f"Please top off your {cocktail_name} with:", True, (255, 255, 255))
    title_rect = title.get_rect(center=(screen_width // 2, screen_height // 4))
    add_layer(title, title_rect, key='top_off_title')

    y_pos = screen_height // 3
    small_font = pygame.font.SysFont(None, 40)
    for ing, amt in manual_ingredients.items():
        text = small_font.render(f"{amt} of {ing}", True, (255, 255, 255))
        rect = text.get_rect(center=(screen_width // 2, y_pos))
        add_layer(text, rect, key=f'top_off_{ing}')
        y_pos += 50

    tap_text = small_font.render("Tap to continue", True, (255, 255, 255))
    tap_rect = tap_text.get_rect(center=(screen_width // 2, screen_height * 3 // 4))
    add_layer(tap_text, tap_rect, key='top_off_tap')

    draw_frame()

    start_time = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                remove_layer('top_off_overlay')
                remove_layer('top_off_title')
                remove_layer('top_off_tap')
                for ing in manual_ingredients:
                    remove_layer(f'top_off_{ing}')
                draw_frame()
                return
        if pygame.time.get_ticks() - start_time > timeout:
            remove_layer('top_off_overlay')
            remove_layer('top_off_title')
            remove_layer('top_off_tap')
            for ing in manual_ingredients:
                remove_layer(f'top_off_{ing}')
            draw_frame()
            return
        clock.tick(60)

def show_enjoy_screen(cocktail_name, timeout=30000):
    """Display an enjoy screen after pouring."""
    overlay = pygame.Surface(screen_size)
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    add_layer(overlay, (0, 0), key='enjoy_overlay')

    font = pygame.font.SysFont(None, 60)
    title = font.render(f"Enjoy your {cocktail_name}!", True, (255, 255, 255))
    title_rect = title.get_rect(center=(screen_width // 2, screen_height // 2))
    add_layer(title, title_rect, key='enjoy_title')

    small_font = pygame.font.SysFont(None, 40)
    tap_text = small_font.render("Tap to continue", True, (255, 255, 255))
    tap_rect = tap_text.get_rect(center=(screen_width // 2, screen_height * 2 // 3))
    add_layer(tap_text, tap_rect, key='enjoy_tap')

    draw_frame()

    start_time = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                remove_layer('enjoy_overlay')
                remove_layer('enjoy_title')
                remove_layer('enjoy_tap')
                draw_frame()
                return
        if pygame.time.get_ticks() - start_time > timeout:
            remove_layer('enjoy_overlay')
            remove_layer('enjoy_title')
            remove_layer('enjoy_tap')
            draw_frame()
            return
        clock.tick(60)

def create_settings_tray():
    """Create the settings tray UI elements"""
    tray_height = int(screen_height * 0.4)  # 40% of screen height
    tray_rect = pygame.Rect(0, screen_height - tray_height, screen_width, tray_height)
    
    # Create a semi-transparent background
    overlay = pygame.Surface((screen_width, tray_height))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    
    # Settings title
    title_font = pygame.font.SysFont(None, 48)
    title_text = title_font.render("Settings", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(screen_width // 2, screen_height - tray_height + 40))
    
    # Time per oz slider
    slider_width = int(screen_width * 0.6)
    slider_height = 20
    slider_x = (screen_width - slider_width) // 2
    slider_y = screen_height - tray_height + 100
    
    # Slider background
    slider_bg_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
    
    # Slider handle position (based on current OZ_COEFFICIENT value)
    min_val, max_val = 1.0, 15.0
    slider_handle_x = slider_x + (OZ_COEFFICIENT - min_val) / (max_val - min_val) * slider_width
    slider_handle_rect = pygame.Rect(slider_handle_x - 10, slider_y - 5, 20, 30)
    
    # Slider label
    slider_font = pygame.font.SysFont(None, 32)
    slider_label = slider_font.render(f"Time per oz: {OZ_COEFFICIENT:.1f}s", True, (255, 255, 255))
    slider_label_rect = slider_label.get_rect(center=(screen_width // 2, slider_y - 30))
    
    # Buttons
    button_width = 150
    button_height = 50
    button_spacing = 20
    
    # Prime pumps button
    prime_rect = pygame.Rect(screen_width // 2 - button_width - button_spacing // 2, 
                           screen_height - tray_height + 180, button_width, button_height)
    prime_font = pygame.font.SysFont(None, 28)
    prime_text = prime_font.render("Prime Pumps", True, (255, 255, 255))
    prime_text_rect = prime_text.get_rect(center=prime_rect.center)
    
    # Clean pumps button
    clean_rect = pygame.Rect(screen_width // 2 + button_spacing // 2, 
                           screen_height - tray_height + 180, button_width, button_height)
    clean_font = pygame.font.SysFont(None, 28)
    clean_text = clean_font.render("Clean Pumps", True, (255, 255, 255))
    clean_text_rect = clean_text.get_rect(center=clean_rect.center)
    
    # Reverse pump direction toggle switch
    switch_width = 60
    switch_height = 30
    switch_x = screen_width // 2 - switch_width // 2
    switch_y = screen_height - tray_height + 250
    
    switch_rect = pygame.Rect(switch_x, switch_y, switch_width, switch_height)
    
    # Switch label
    switch_font = pygame.font.SysFont(None, 24)
    switch_label = switch_font.render("Reverse Pump Direction", True, (255, 255, 255))
    switch_label_rect = switch_label.get_rect(center=(screen_width // 2, switch_y - 20))
    
    # Streamlit app access info
    import socket
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"
    
    streamlit_port = 8501  # Default Streamlit port
    
    # Access info label
    access_font = pygame.font.SysFont(None, 20)
    access_label = access_font.render("Access your app at:", True, (200, 200, 200))
    access_label_rect = access_label.get_rect(center=(screen_width // 2, switch_y + 50))
    
    # IP and port info
    ip_font = pygame.font.SysFont(None, 24)
    ip_text = f"http://{local_ip}:{streamlit_port}"
    ip_label = ip_font.render(ip_text, True, (0, 255, 255))  # Cyan color for URL
    ip_label_rect = ip_label.get_rect(center=(screen_width // 2, switch_y + 75))
    
    return {
        'tray_rect': tray_rect,
        'overlay': overlay,
        'title_text': title_text,
        'title_rect': title_rect,
        'slider_bg_rect': slider_bg_rect,
        'slider_handle_rect': slider_handle_rect,
        'slider_label': slider_label,
        'slider_label_rect': slider_label_rect,
        'prime_rect': prime_rect,
        'prime_text': prime_text,
        'prime_text_rect': prime_text_rect,
        'clean_rect': clean_rect,
        'clean_text': clean_text,
        'clean_text_rect': clean_text_rect,
        'switch_rect': switch_rect,
        'switch_label': switch_label,
        'switch_label_rect': switch_label_rect,
        'access_label': access_label,
        'access_label_rect': access_label_rect,
        'ip_label': ip_label,
        'ip_label_rect': ip_label_rect,
        'slider_x': slider_x,
        'slider_width': slider_width,
        'min_val': min_val,
        'max_val': max_val
    }

def draw_settings_tray(settings_ui, is_visible):
    """Draw the settings tray if visible"""
    if not is_visible:
        return
    
    # Draw overlay
    add_layer(settings_ui['overlay'], settings_ui['tray_rect'], key='settings_overlay')
    
    # Draw title
    add_layer(settings_ui['title_text'], settings_ui['title_rect'], key='settings_title')
    
    # Create temporary surfaces for slider and buttons
    temp_surface = pygame.Surface(screen_size, pygame.SRCALPHA)
    
    # Draw slider background
    pygame.draw.rect(temp_surface, (100, 100, 100), settings_ui['slider_bg_rect'])
    
    # Draw slider handle
    pygame.draw.rect(temp_surface, (255, 255, 255), settings_ui['slider_handle_rect'])
    
    # Draw buttons
    pygame.draw.rect(temp_surface, (50, 150, 50), settings_ui['prime_rect'])
    pygame.draw.rect(temp_surface, (150, 50, 50), settings_ui['clean_rect'])
    
    # Draw switch background
    switch_color = (0, 200, 0) if INVERT_PUMP_PINS else (100, 100, 100)
    pygame.draw.rect(temp_surface, switch_color, settings_ui['switch_rect'])
    pygame.draw.rect(temp_surface, (200, 200, 200), settings_ui['switch_rect'], 2)
    
    # Draw switch indicator (circle)
    indicator_radius = 12
    if INVERT_PUMP_PINS:
        # ON position - indicator on the right
        indicator_x = settings_ui['switch_rect'].x + settings_ui['switch_rect'].width - indicator_radius - 3
    else:
        # OFF position - indicator on the left
        indicator_x = settings_ui['switch_rect'].x + indicator_radius + 3
    indicator_y = settings_ui['switch_rect'].y + settings_ui['switch_rect'].height // 2
    pygame.draw.circle(temp_surface, (255, 255, 255), (indicator_x, indicator_y), indicator_radius)
    
    add_layer(temp_surface, (0, 0), key='settings_controls')
    
    # Draw slider label
    add_layer(settings_ui['slider_label'], settings_ui['slider_label_rect'], key='slider_label')
    
    # Draw button text
    add_layer(settings_ui['prime_text'], settings_ui['prime_text_rect'], key='prime_text')
    add_layer(settings_ui['clean_text'], settings_ui['clean_text_rect'], key='clean_text')
    
    # Draw switch label
    add_layer(settings_ui['switch_label'], settings_ui['switch_label_rect'], key='switch_label')
    
    # Draw access info
    add_layer(settings_ui['access_label'], settings_ui['access_label_rect'], key='access_label')
    add_layer(settings_ui['ip_label'], settings_ui['ip_label_rect'], key='ip_label')

def create_settings_tab():
    """Create the small tab at the bottom for accessing settings"""
    tab_width = 80
    tab_height = 20
    tab_x = (screen_width - tab_width) // 2
    tab_y = screen_height - tab_height
    
    tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
    
    # Create simple tab surface
    tab_surface = pygame.Surface((tab_width, tab_height))
    tab_surface.fill((60, 60, 60))  # Dark gray
    
    # Add border for definition
    pygame.draw.rect(tab_surface, (120, 120, 120), (0, 0, tab_width, tab_height), 2)
    
    return {
        'rect': tab_rect,
        'surface': tab_surface,
        'base_y': tab_y,  # Store original position
        'width': tab_width,
        'height': tab_height
    }

def animate_settings_tray(settings_ui, settings_tab, show_tray, duration=300):
    """Animate the settings tray sliding up or down"""
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    tray_height = settings_ui['tray_rect'].height
    
    if show_tray:
        # Slide up from bottom
        start_y = screen_height
        end_y = screen_height - tray_height
        tab_start_y = settings_tab['base_y']
        tab_end_y = screen_height - tray_height - settings_tab['height']
    else:
        # Slide down to bottom
        start_y = screen_height - tray_height
        end_y = screen_height
        tab_start_y = screen_height - tray_height - settings_tab['height']
        tab_end_y = settings_tab['base_y']
    
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        
        current_y = start_y + (end_y - start_y) * progress
        settings_ui['tray_rect'].y = current_y
        
        # Update tab position to slide with tray
        tab_current_y = tab_start_y + (tab_end_y - tab_start_y) * progress
        settings_tab['rect'].y = tab_current_y
        
        # Update all related positions
        settings_ui['title_rect'].y = current_y + 40
        settings_ui['slider_bg_rect'].y = current_y + 100
        settings_ui['slider_handle_rect'].y = current_y + 95
        settings_ui['slider_label_rect'].y = current_y + 70
        settings_ui['prime_rect'].y = current_y + 180
        settings_ui['clean_rect'].y = current_y + 180
        settings_ui['prime_text_rect'].center = settings_ui['prime_rect'].center
        settings_ui['clean_text_rect'].center = settings_ui['clean_rect'].center
        settings_ui['switch_rect'].y = current_y + 250
        settings_ui['switch_label_rect'].y = current_y + 230
        settings_ui['access_label_rect'].y = current_y + 300
        settings_ui['ip_label_rect'].y = current_y + 325
        
        # Update tab layer
        remove_layer('settings_tab')
        add_layer(settings_tab['surface'], settings_tab['rect'], key='settings_tab')
        
        draw_settings_tray(settings_ui, True)
        draw_frame()
        
        if progress >= 1.0:
            break
        clock.tick(60)

def handle_settings_interaction(settings_ui, event_pos):
    """Handle interactions with settings tray elements"""
    # Check if slider is being dragged
    if settings_ui['slider_handle_rect'].collidepoint(event_pos):
        return 'slider_drag'
    
    # Check if prime button is clicked
    if settings_ui['prime_rect'].collidepoint(event_pos):
        return 'prime_pumps'
    
    # Check if clean button is clicked
    if settings_ui['clean_rect'].collidepoint(event_pos):
        return 'clean_pumps'
    
    # Check if switch is clicked
    if settings_ui['switch_rect'].collidepoint(event_pos):
        return 'toggle_switch'
    
    return None

def update_oz_coefficient(settings_ui, new_value):
    """Update the OZ_COEFFICIENT setting and slider position"""
    global OZ_COEFFICIENT
    OZ_COEFFICIENT = max(settings_ui['min_val'], min(settings_ui['max_val'], new_value))
    
    # Update slider handle position
    slider_handle_x = settings_ui['slider_x'] + (OZ_COEFFICIENT - settings_ui['min_val']) / (settings_ui['max_val'] - settings_ui['min_val']) * settings_ui['slider_width']
    settings_ui['slider_handle_rect'].x = slider_handle_x - 10
    
    # Update slider label
    slider_font = pygame.font.SysFont(None, 32)
    settings_ui['slider_label'] = slider_font.render(f"Time per oz: {OZ_COEFFICIENT:.1f}s", True, (255, 255, 255))

def toggle_pump_direction():
    """Toggle the INVERT_PUMP_PINS setting"""
    global INVERT_PUMP_PINS
    INVERT_PUMP_PINS = not INVERT_PUMP_PINS
    logger.info(f'Pump direction inverted: {INVERT_PUMP_PINS}')

def generate_new_drink_menu():
    """Generate a new drink menu using OpenAI"""
    import openai
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found")
        return
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = """Create a comprehensive list of as many unique and interesting cocktail ingredients as possible. 
        Focus on spirits, liqueurs, juices, syrups, and mixers that would be commonly used in cocktails.
        Include both alcoholic and non-alcoholic ingredients.
        Make sure to include a wide variety of options for a well-stocked bar.
        Return only the list of ingredients, one per line, in alphabetical order."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cocktail expert. Provide comprehensive lists of cocktail ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        # Parse the response and update drink options
        new_drinks = [""] + [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]
        
        # Update drink_options.json
        with open('drink_options.json', 'w') as f:
            json.dump({"drinks": new_drinks}, f, indent=2)
        
        logger.info(f"Generated {len(new_drinks)-1} new drink options")
        return new_drinks
        
    except Exception as e:
        logger.error(f"Error generating drink menu: {e}")
        return None

def run_interface():

    def load_cocktail_image(cocktail):
        """Given a Cocktail object, load the image for that cocktail and scale it to the screen size"""
        if cocktail.get('is_qr_slide'):
            # For QR code slides, use the QR surface directly
            qr_surface = cocktail.get('qr_surface')
            if qr_surface:
                qr_scale = 0.25  # Scale down QR by 25%
                scaled = pygame.transform.scale(qr_surface, (int(screen_width * COCKTAIL_IMAGE_SCALE * qr_scale), int(screen_height * COCKTAIL_IMAGE_SCALE * qr_scale)))
                # Centered rect will be applied where added
                return scaled
            else:
                return None
        
        # Regular cocktail image loading (case-insensitive on filesystems)
        path = get_cocktail_image_path(cocktail)
        try:
            # Resolve path case-insensitively for Linux/Pi
            logo_dir = os.path.dirname(path)
            expected = os.path.basename(path).lower()
            resolved_path = None
            if os.path.isdir(logo_dir):
                for fname in os.listdir(logo_dir):
                    if fname.lower() == expected:
                        resolved_path = os.path.join(logo_dir, fname)
                        break
            if not resolved_path:
                logger.error(f"Logo not found (case-insensitive): {path}")
                return None
            img = pygame.image.load(resolved_path)
            common_scale = 0.5  # Scale all cocktails by 50% to match QR sizing
            img = pygame.transform.scale(
                img,
                (int(screen_width * COCKTAIL_IMAGE_SCALE * common_scale), int(screen_height * COCKTAIL_IMAGE_SCALE * common_scale))
            )
            return img
        except Exception as e:
            logger.exception(f'Error loading {path}')
            return None

    def load_cocktail(index):
        """Load a cocktail based on a provided index. Also pre-load the images for the previous and next cocktails"""
        current_cocktail = cocktails[index]
        current_image = load_cocktail_image(current_cocktail)
        current_cocktail_name = current_cocktail.get('normal_name', '')
        previous_cocktail = cocktails[(index - 1) % len(cocktails)]
        previous_image = load_cocktail_image(previous_cocktail)
        next_cocktail = cocktails[(index + 1) % len(cocktails)]
        next_image = load_cocktail_image(next_cocktail)
        return current_cocktail, current_image, current_cocktail_name, previous_image, next_image

    # Load the static background image (tipsy.jpg)
    try:
        background = pygame.image.load('./tipsy.jpg')
        background = pygame.transform.scale(background, screen_size)
        add_layer(background, (0, 0), key='background')
    except Exception as e:
        logger.exception('Error loading background image (tipsy.jpg)')
        add_layer((0, 0), function=screen.fill, key='background')
    
    cocktails = get_cocktails_with_qr()
    
    if not cocktails:
        logger.critical('No valid cocktails found in cocktails.json')
        pygame.quit()
        return
    current_index = 0
    current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)
    reload_time = pygame.time.get_ticks()

    margin = 50  # adjust as needed for spacing
    # Load single & double buttons and scale them to 75% of original (base size: 150x150)
    try:
        single_logo = pygame.image.load('nav-photos/single.png')
        single_logo = pygame.transform.scale(single_logo, (150, 150))
        single_rect = pygame.Rect(margin, (screen_height - 150) // 2, 150, 150)
        add_layer(single_logo, single_rect, key='single_logo')
    except Exception as e:
        logger.exception('Error loading nav-photos/single.png:')
        single_logo = None
    try:
        double_logo = pygame.image.load('nav-photos/double.png')
        double_logo = pygame.transform.scale(double_logo, (150, 150))
        double_rect = pygame.Rect(screen_width - margin - 150, (screen_height - 150) // 2, 150, 150)
        add_layer(double_logo, double_rect, key='double_logo')
    except Exception as e:
        logger.exception('Error loading nav-photos/double.png')
        double_logo = None
    if ALLOW_FAVORITES:
        favorite_rect = pygame.Rect(screen_width - (margin * 3), 150, 150, 150)
        try:
            favorite_logo = pygame.image.load('nav-photos/favorite.png')
            favorite_logo = pygame.transform.scale(favorite_logo, (50, 50))
        except Exception:
            logger.exception('Error loading nav-photos/favorite.png')
            favorite_logo = None
        try:
            unfavorite_logo = pygame.image.load('nav-photos/unfavorite.png')
            unfavorite_logo = pygame.transform.scale(unfavorite_logo, (50, 50))
        except Exception:
            logger.exception('Error loading nav-photos/unfavorite.png')
            unfavorite_logo = None
    else:
        favorite_rect = None
        favorite_logo = None
        unfavorite_logo = None
    if SHOW_RELOAD_COCKTAILS_BUTTON:
        reload_cocktails_rect = pygame.Rect(margin * 2, 150, 50, 50)
        try:
            reload_logo = pygame.image.load('nav-photos/reload.png')
            reload_logo = pygame.transform.scale(reload_logo, (50, 50))
            add_layer(reload_logo, reload_cocktails_rect, key='reload_logo')
        except Exception as e:
            logger.exception('Error loading nav-photos/reload.png')
            reload_logo = None
    else:
        reload_cocktails_rect = None
        reload_logo = None

    # Initialize settings tray and tab
    settings_ui = create_settings_tray()
    settings_tab = create_settings_tab()
    settings_visible = False
    slider_dragging = False
    tab_dragging = False
    tab_drag_start_y = 0
    
    # Add tabs to layers
    add_layer(settings_tab['surface'], settings_tab['rect'], key='settings_tab')

    dragging = False
    drag_start_x = 0
    drag_offset = 0
    clock = pygame.time.Clock()

    running = True
    last_refresh_check = pygame.time.get_ticks()
    refresh_check_interval = 1000  # Check every 1 second
    
    while running:
        # Check for refresh signals periodically
        current_time = pygame.time.get_ticks()
        if current_time - last_refresh_check > refresh_check_interval:
            if check_for_refresh_signal():
                logger.info("Refreshing cocktails due to app signal")
                cocktails = get_cocktails_with_qr()
                current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)
            last_refresh_check = current_time
        
        events = pygame.event.get()
        for event in events:
            # Handle dropdown events globally if drink tray is visible
            # The drink management tray is removed, so this block is no longer relevant.
            
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if settings tab is clicked or dragged
                if settings_tab['rect'].collidepoint(event.pos):
                    tab_dragging = True
                    tab_drag_start_y = event.pos[1]
                    continue
                
                # Check if settings tray is clicked
                if settings_visible and settings_ui['tray_rect'].collidepoint(event.pos):
                    interaction = handle_settings_interaction(settings_ui, event.pos)
                    if interaction == 'slider_drag':
                        slider_dragging = True
                    elif interaction == 'prime_pumps':
                        # Import and call prime_pumps function
                        from controller import prime_pumps
                        prime_pumps(duration=10)
                    elif interaction == 'clean_pumps':
                        # Import and call clean_pumps function
                        from controller import clean_pumps
                        clean_pumps(duration=10)
                    elif interaction == 'toggle_switch':
                        # Toggle pump direction
                        toggle_pump_direction()
                    continue
                
                # If settings is visible and clicked outside, close it
                if settings_visible:
                    settings_visible = False
                    animate_settings_tray(settings_ui, settings_tab, settings_visible)
                    continue
                
                dragging = True
                drag_start_x = event.pos[0]
            if event.type == pygame.MOUSEMOTION:
                if tab_dragging:
                    # Handle tab drag to open/close settings
                    current_y = event.pos[1]
                    drag_distance = tab_drag_start_y - current_y
                    
                    # If dragged up enough, open settings
                    if drag_distance > 50 and not settings_visible:
                        settings_visible = True
                        animate_settings_tray(settings_ui, settings_tab, settings_visible)
                        tab_dragging = False
                    # If dragged down enough, close settings  
                    elif drag_distance < -30 and settings_visible:
                        settings_visible = False
                        animate_settings_tray(settings_ui, settings_tab, settings_visible)
                        tab_dragging = False
                elif slider_dragging:
                    # Update slider based on mouse position
                    mouse_x = event.pos[0]
                    slider_x = settings_ui['slider_x']
                    slider_width = settings_ui['slider_width']
                    
                    # Calculate new value
                    relative_x = max(0, min(slider_width, mouse_x - slider_x))
                    new_value = settings_ui['min_val'] + (relative_x / slider_width) * (settings_ui['max_val'] - settings_ui['min_val'])
                    update_oz_coefficient(settings_ui, new_value)
                elif dragging:
                    current_x = event.pos[0]
                    drag_offset = current_x - drag_start_x
            if event.type == pygame.MOUSEBUTTONUP:
                if tab_dragging:
                    # If tab was clicked without significant drag, toggle settings
                    current_y = event.pos[1]
                    drag_distance = abs(tab_drag_start_y - current_y)
                    if drag_distance < 10:  # Minimal movement, treat as click
                        settings_visible = not settings_visible
                        animate_settings_tray(settings_ui, settings_tab, settings_visible)
                    tab_dragging = False
                    continue
                elif slider_dragging:
                    slider_dragging = False
                    continue
                elif dragging:
                    # If it's a click (minimal drag), check extra logos.
                    if abs(drag_offset) < 10:
                        pos = event.pos
                        if single_rect.collidepoint(pos):
                            if current_cocktail.get('is_qr_slide'):
                                continue
                            # Animate single logo click
                            if single_logo:
                                animate_logo_click(single_logo, single_rect, base_size=150, target_size=220, layer_key='single_logo', duration=150)

                            executor_watcher, manual_ingredients = make_drink(current_cocktail, 'single')
                            if executor_watcher is None:
                                continue

                            show_pouring_and_loading(executor_watcher)

                            if manual_ingredients:
                                show_top_off_screen(manual_ingredients, current_cocktail_name)

                            show_enjoy_screen(current_cocktail_name)

                        elif double_rect.collidepoint(pos):
                            if current_cocktail.get('is_qr_slide'):
                                continue
                            # Animate double logo click
                            if double_logo:
                                animate_logo_click(double_logo, double_rect, base_size=150, target_size=220, layer_key='double_logo', duration=150)

                            executor_watcher, manual_ingredients = make_drink(current_cocktail, 'double')
                            if executor_watcher is None:
                                continue

                            show_pouring_and_loading(executor_watcher)

                            if manual_ingredients:
                                show_top_off_screen(manual_ingredients, current_cocktail_name)

                            show_enjoy_screen(current_cocktail_name)
                    
                        elif reload_cocktails_rect and reload_cocktails_rect.collidepoint(pos):
                            logger.debug('Reloading cocktails due to reload button press')
                            animate_logo_rotate(reload_logo, reload_cocktails_rect, layer_key='reload_logo')
                            cocktails = get_cocktails_with_qr()
                            current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)

                        elif favorite_rect and favorite_rect.collidepoint(pos):
                            if current_cocktail.get('favorite'):
                                logger.debug(f'Unfavoriting current cocktail: {current_index}')
                                current_index = unfavorite_cocktail(current_index)
                            else:
                                logger.debug(f'Favoriting current cocktail: {current_index}')
                                current_index = favorite_cocktail(current_index)
                                
                            cocktails = get_cocktails_with_qr()
                            current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)
                            
                        dragging = False
                        drag_offset = 0
                        continue  # Skip further swipe handling.
                    # Otherwise, it's a swipe.
                    if abs(drag_offset) > screen_width / 4:
                        if drag_offset < 0:
                            target_offset = -screen_width
                            new_index = (current_index + 1) % len(cocktails)
                        else:
                            target_offset = screen_width
                            new_index = (current_index - 1) % len(cocktails)
                        start_offset = drag_offset
                        duration = 300
                        start_time = pygame.time.get_ticks()
                        while True:
                            elapsed = pygame.time.get_ticks() - start_time
                            progress = min(elapsed / duration, 1.0)
                            current_offset = start_offset + (target_offset - start_offset) * progress
                            add_layer(
                                current_image,
                                get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=current_offset).topleft,
                                key='current_cocktail'
                            )
                            if drag_offset < 0:
                                if next_image is not None:
                                    add_layer(
                                        next_image,
                                        get_centered_rect_for_surface(next_image, screen_width, screen_height, offset_x=screen_width + current_offset).topleft,
                                        key='next_cocktail'
                                    )
                            else:
                                if previous_image is not None:
                                    add_layer(
                                        previous_image,
                                        get_centered_rect_for_surface(previous_image, screen_width, screen_height, offset_x=-screen_width + current_offset).topleft,
                                        key='previous_cocktail'
                                    )
                            draw_frame()
                            if progress >= 1.0:
                                break
                            clock.tick(60)
                        current_index = new_index
                        current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)

                        # Animate both extra logos zooming together.
                        if single_logo and double_logo:
                            animate_both_logos_zoom(single_logo, double_logo, single_rect, double_rect, base_size=150, target_size=175, duration=300)
                    else:
                        # Animate snapping back if swipe is insufficient.
                        start_offset = drag_offset
                        duration = 300
                        start_time = pygame.time.get_ticks()
                        while True:
                            elapsed = pygame.time.get_ticks() - start_time
                            progress = min(elapsed / duration, 1.0)
                            current_offset = start_offset * (1 - progress)
                            add_layer(
                                current_image,
                                get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=current_offset).topleft,
                                key='current_cocktail'
                            )
                            # Text just below the current image with padding
                            is_qr = current_cocktail.get('is_qr_slide')
                            label_font_size = 32 if is_qr else 60
                            font = pygame.font.SysFont(None, label_font_size)
                            drink_name = current_cocktail.get('url', 'Scan QR Code') if is_qr else current_cocktail_name
                            text_surface = font.render(drink_name, True, (255, 255, 255))
                            image_rect = get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=current_offset)
                            text_rect = text_surface.get_rect(midtop=(screen_width // 2, image_rect.bottom + 24))
                            add_layer(text_surface, text_rect, key='cocktail_name')
                            draw_frame()
                            if progress >= 1.0:
                                break
                            clock.tick(60)
                    dragging = False
                    drag_offset = 0

        # Main drawing (when not in special animation)
        if RELOAD_COCKTAILS_TIMEOUT and pygame.time.get_ticks() - reload_time > RELOAD_COCKTAILS_TIMEOUT:
            logger.debug('Reloading cocktails due to auto reload timeout')
            cocktails = get_cocktails_with_qr()
            current_cocktail, current_image, current_cocktail_name, previous_image, next_image = load_cocktail(current_index)
            reload_time = pygame.time.get_ticks()

        if dragging:
            remove_layer('cocktail_name')
            remove_layer('favorite_logo')
            add_layer(
                current_image,
                get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=drag_offset).topleft,
                key='current_cocktail'
            )
            if drag_offset < 0:
                if next_image is not None:
                    add_layer(
                        next_image,
                        get_centered_rect_for_surface(next_image, screen_width, screen_height, offset_x=screen_width + drag_offset).topleft,
                        key='next_cocktail'
                    )
            elif drag_offset > 0:
                if previous_image is not None:
                    add_layer(
                        previous_image,
                        get_centered_rect_for_surface(previous_image, screen_width, screen_height, offset_x=-screen_width + drag_offset).topleft,
                        key='previous_cocktail'
                    )
        else:
            remove_layer('next_cocktail')
            remove_layer('previous_cocktail')
            add_layer(
                current_image,
                get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=0).topleft,
                key='current_cocktail'
            )
            # Text just below the current image with padding
            is_qr = current_cocktail.get('is_qr_slide')
            label_font_size = 32 if is_qr else 60
            font = pygame.font.SysFont(None, label_font_size)
            drink_name = current_cocktail.get('url', 'Scan QR Code') if is_qr else current_cocktail_name
            text_surface = font.render(drink_name, True, (255, 255, 255))
            image_rect = get_centered_rect_for_surface(current_image, screen_width, screen_height, offset_x=0)
            text_rect = text_surface.get_rect(midtop=(screen_width // 2, image_rect.bottom + 24))
            add_layer(text_surface, text_rect, key='cocktail_name')
            if ALLOW_FAVORITES:
                if current_cocktail.get('favorite', False) and favorite_logo:
                    add_layer(favorite_logo, favorite_rect, key='favorite_logo')
                elif unfavorite_logo:
                    add_layer(unfavorite_logo, favorite_rect, key='favorite_logo')
        
        # Update tab positions when not animating
        if not tab_dragging:
            if settings_visible:
                # Tab should be at the top of the tray
                settings_tab['rect'].y = settings_ui['tray_rect'].y - settings_tab['height']
            else:
                # Tab should be at the bottom
                settings_tab['rect'].y = settings_tab['base_y']
            
            # Update settings tab layer
            remove_layer('settings_tab')
            add_layer(settings_tab['surface'], settings_tab['rect'], key='settings_tab')
        
        # Draw settings tray if visible
        if settings_visible:
            draw_settings_tray(settings_ui, True)
        
        draw_frame()
        
        # Draw custom dropdowns AFTER draw_frame() so they appear on top
        # The drink management tray is removed, so this block is no longer relevant.
        
        clock.tick(60)
    pygame.quit()

if __name__ == '__main__':
    run_interface()
