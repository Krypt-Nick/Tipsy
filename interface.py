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

class CustomDropdown:
    """Custom dropdown implementation to replace pygame_widgets"""
    def __init__(self, x, y, width, height, options, current_value="", font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.current_value = current_value
        self.font = pygame.font.SysFont(None, font_size)
        self.is_open = False
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 5
        self.item_height = 30
        
        # Find current value index
        if current_value in options:
            self.selected_index = options.index(current_value)
    
    def handle_event(self, event):
        """Handle mouse events for the dropdown"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            elif self.is_open:
                # Check if clicking on dropdown items
                dropdown_rect = pygame.Rect(
                    self.rect.x, 
                    self.rect.y + self.rect.height,
                    self.rect.width, 
                    min(len(self.options), self.max_visible_items) * self.item_height
                )
                if dropdown_rect.collidepoint(event.pos):
                    # Calculate which item was clicked
                    relative_y = event.pos[1] - dropdown_rect.y
                    item_index = relative_y // self.item_height + self.scroll_offset
                    if 0 <= item_index < len(self.options):
                        self.selected_index = item_index
                        self.current_value = self.options[item_index]
                        self.is_open = False
                        return True
                else:
                    self.is_open = False
        
        elif event.type == pygame.MOUSEWHEEL and self.is_open:
            # Handle scrolling in dropdown
            dropdown_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + self.rect.height,
                self.rect.width, 
                min(len(self.options), self.max_visible_items) * self.item_height
            )
            if dropdown_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, min(
                    len(self.options) - self.max_visible_items,
                    self.scroll_offset - event.y
                ))
                return True
        
        return False
    
    def draw(self, surface):
        """Draw the dropdown"""
        # Draw main dropdown button
        pygame.draw.rect(surface, (240, 240, 240), self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)
        
        # Draw current selection text
        display_text = self.current_value if self.current_value else "Select..."
        if len(display_text) > 20:
            display_text = display_text[:17] + "..."
        text_surface = self.font.render(display_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery))
        surface.blit(text_surface, text_rect)
        
        # Draw dropdown arrow
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery + 5),
            (self.rect.right - 30, self.rect.centery + 5)
        ]
        pygame.draw.polygon(surface, (0, 0, 0), arrow_points)
        
        # Draw dropdown list if open
        if self.is_open:
            visible_items = min(len(self.options), self.max_visible_items)
            dropdown_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + self.rect.height,
                self.rect.width, 
                visible_items * self.item_height
            )
            
            # Draw dropdown background
            pygame.draw.rect(surface, (255, 255, 255), dropdown_rect)
            pygame.draw.rect(surface, (100, 100, 100), dropdown_rect, 2)
            
            # Draw items
            for i in range(visible_items):
                item_index = i + self.scroll_offset
                if item_index >= len(self.options):
                    break
                    
                item_rect = pygame.Rect(
                    dropdown_rect.x,
                    dropdown_rect.y + i * self.item_height,
                    dropdown_rect.width,
                    self.item_height
                )
                
                # Highlight selected item
                if item_index == self.selected_index:
                    pygame.draw.rect(surface, (200, 220, 255), item_rect)
                
                # Highlight hovered item
                mouse_pos = pygame.mouse.get_pos()
                if item_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, (230, 240, 255), item_rect)
                
                # Draw item text
                item_text = self.options[item_index]
                if len(item_text) > 25:
                    item_text = item_text[:22] + "..."
                text_surface = self.font.render(item_text, True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=item_rect.center)
                surface.blit(text_surface, text_rect)
                
                # Draw separator line
                if i < visible_items - 1:
                    pygame.draw.line(surface, (200, 200, 200), 
                                   (item_rect.left, item_rect.bottom), 
                                   (item_rect.right, item_rect.bottom))
            
            # Draw scrollbar if needed
            if len(self.options) > self.max_visible_items:
                scrollbar_rect = pygame.Rect(
                    dropdown_rect.right - 10,
                    dropdown_rect.y,
                    10,
                    dropdown_rect.height
                )
                pygame.draw.rect(surface, (200, 200, 200), scrollbar_rect)
                
                # Calculate scrollbar thumb
                thumb_height = max(20, dropdown_rect.height * self.max_visible_items // len(self.options))
                thumb_y = dropdown_rect.y + (dropdown_rect.height - thumb_height) * self.scroll_offset // (len(self.options) - self.max_visible_items)
                thumb_rect = pygame.Rect(scrollbar_rect.x, thumb_y, scrollbar_rect.width, thumb_height)
                pygame.draw.rect(surface, (100, 100, 100), thumb_rect)
    
    def get_selected(self):
        """Get the currently selected value"""
        return self.current_value

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

def create_drink_management_tray():
    """Create the drink management tray UI elements"""
    tray_height = int(screen_height * 0.8)  # 80% of screen height
    tray_rect = pygame.Rect(0, -tray_height, screen_width, tray_height)
    
    # Create a gradient background for better aesthetics
    overlay = pygame.Surface((screen_width, tray_height))
    overlay.set_alpha(220)
    # Create gradient effect
    for y in range(tray_height):
        alpha = int(255 * (1 - y / tray_height) * 0.8)
        color = (20, 25, 35)
        pygame.draw.line(overlay, color, (0, y), (screen_width, y))
    
    # Header section with better styling
    header_height = 80
    header_surface = pygame.Surface((screen_width, header_height))
    header_surface.set_alpha(180)
    header_surface.fill((25, 30, 40))
    
    # Title with shadow effect
    title_font = pygame.font.SysFont('Arial', 42, bold=True)
    title_shadow = title_font.render("Drink Management", True, (0, 0, 0))
    title_text = title_font.render("Drink Management", True, (255, 255, 255))
    title_shadow_rect = title_shadow.get_rect(center=(screen_width // 2 + 2, 42))
    title_rect = title_text.get_rect(center=(screen_width // 2, 40))
    
    # Load drink options
    try:
        with open('drink_options.json', 'r') as f:
            drink_data = json.load(f)
            drink_options = drink_data['drinks']
        print(f"Loaded {len(drink_options)} drink options from JSON")
    except Exception as e:
        print(f"Error loading drink options: {e}")
        drink_options = ["", "Vodka", "Gin", "Rum", "Tequila", "Whiskey", "Bourbon", "Scotch", "Brandy", "Cognac"]
        print(f"Using fallback options: {len(drink_options)} drinks")
    
    # Load current pump configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            current_config = json.load(f)
    except:
        current_config = {}
    
    # Create custom dropdowns for 12 pumps with better layout
    dropdowns = []
    dropdown_width = 180  # Slightly smaller for better fit
    dropdown_height = 45
    dropdown_spacing = 25
    
    # Calculate positions for a more organized 6x2 grid
    total_width = 6 * dropdown_width + 5 * dropdown_spacing
    start_x = (screen_width - total_width) // 2
    
    # Top row (pumps 1-6) - with better spacing
    top_row_y = header_height + 40
    for i in range(6):
        x = start_x + i * (dropdown_width + dropdown_spacing)
        y = top_row_y
        
        # Styled pump label
        label_font = pygame.font.SysFont('Arial', 20, bold=True)
        label_text = label_font.render(f"Pump {i+1}", True, (220, 220, 220))
        label_rect = label_text.get_rect(center=(x + dropdown_width // 2, y - 15))
        
        # Current selection
        current_drink = current_config.get(f"Pump {i+1}", "")
        
        # Create custom dropdown
        dropdown = CustomDropdown(
            x, y, dropdown_width, dropdown_height,
            drink_options, current_drink, font_size=16
        )
        print(f"Created dropdown for Pump {i+1} at ({x}, {y}) with {len(drink_options)} options")
        
        dropdowns.append({
            'dropdown': dropdown,
            'label_text': label_text,
            'label_rect': label_rect,
            'current_value': current_drink,
            'pump_number': i+1,
            'rect': pygame.Rect(x, y, dropdown_width, dropdown_height)
        })
    
    # Bottom row (pumps 7-12) - with better spacing
    bottom_row_y = top_row_y + 120
    for i in range(6):
        x = start_x + i * (dropdown_width + dropdown_spacing)
        y = bottom_row_y
        
        # Styled pump label
        label_font = pygame.font.SysFont('Arial', 20, bold=True)
        label_text = label_font.render(f"Pump {i+7}", True, (220, 220, 220))
        label_rect = label_text.get_rect(center=(x + dropdown_width // 2, y - 15))
        
        # Current selection
        current_drink = current_config.get(f"Pump {i+7}", "")
        
        # Create custom dropdown
        dropdown = CustomDropdown(
            x, y, dropdown_width, dropdown_height,
            drink_options, current_drink, font_size=16
        )
        print(f"Created dropdown for Pump {i+7} at ({x}, {y}) with {len(drink_options)} options")
        
        dropdowns.append({
            'dropdown': dropdown,
            'label_text': label_text,
            'label_rect': label_rect,
            'current_value': current_drink,
            'pump_number': i+7,
            'rect': pygame.Rect(x, y, dropdown_width, dropdown_height)
        })
    
    # Styled Generate button at the bottom
    generate_button_width = 250
    generate_button_height = 55
    generate_button_x = (screen_width - generate_button_width) // 2
    generate_button_y = bottom_row_y + 150
    
    generate_button_rect = pygame.Rect(generate_button_x, generate_button_y, generate_button_width, generate_button_height)
    generate_font = pygame.font.SysFont('Arial', 24, bold=True)
    generate_text = generate_font.render("Generate New Menu", True, (255, 255, 255))
    generate_text_rect = generate_text.get_rect(center=generate_button_rect.center)
    
    return {
        'tray_rect': tray_rect,
        'overlay': overlay,
        'header_surface': header_surface,
        'title_text': title_text,
        'title_shadow': title_shadow,
        'title_rect': title_rect,
        'title_shadow_rect': title_shadow_rect,
        'dropdowns': dropdowns,
        'generate_button_rect': generate_button_rect,
        'generate_text': generate_text,
        'generate_text_rect': generate_text_rect
    }

def create_drink_management_tab():
    """Create the small tab at the top for accessing drink management"""
    tab_width = 80
    tab_height = 20
    tab_x = (screen_width - tab_width) // 2
    tab_y = 0
    
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

def draw_drink_management_tray(drink_ui, is_visible, events=None):
    """Draw the drink management tray if visible"""
    if not is_visible:
        return
    
    # Draw gradient background overlay
    add_layer(drink_ui['overlay'], drink_ui['tray_rect'], key='drink_overlay')
    
    # Draw header section
    header_rect = pygame.Rect(drink_ui['tray_rect'].x, drink_ui['tray_rect'].y, 
                             drink_ui['tray_rect'].width, 80)
    add_layer(drink_ui['header_surface'], header_rect, key='drink_header')
    
    # Draw title with shadow effect
    add_layer(drink_ui['title_shadow'], drink_ui['title_shadow_rect'], key='drink_title_shadow')
    add_layer(drink_ui['title_text'], drink_ui['title_rect'], key='drink_title')
    
    # Draw pump labels with better styling
    for dropdown in drink_ui['dropdowns']:
        add_layer(dropdown['label_text'], dropdown['label_rect'], key=f'label_{dropdown["pump_number"]}')
    
    # Note: Custom dropdowns will be drawn after draw_frame() to ensure they're on top
    
    # Draw styled generate button with gradient and border
    button_rect = drink_ui['generate_button_rect']
    
    # Button gradient background
    for i in range(button_rect.height):
        color_ratio = i / button_rect.height
        color = (
            int(40 + (80 - 40) * color_ratio),   # Dark green to lighter green
            int(120 + (160 - 120) * color_ratio),
            int(40 + (80 - 40) * color_ratio)
        )
        pygame.draw.line(screen, color, 
                        (button_rect.left, button_rect.top + i), 
                        (button_rect.right, button_rect.top + i))
    
    # Button border and highlight
    pygame.draw.rect(screen, (100, 200, 100), button_rect, 3)
    pygame.draw.rect(screen, (150, 220, 150), button_rect, 1)
    
    # Button text
    add_layer(drink_ui['generate_text'], drink_ui['generate_text_rect'], key='generate_text')

def animate_drink_management_tray(drink_ui, drink_tab, show_tray, duration=300):
    """Animate the drink management tray sliding down or up"""
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    tray_height = drink_ui['tray_rect'].height
    
    if show_tray:
        # Slide down from top
        start_y = -tray_height
        end_y = 0
        tab_start_y = drink_tab['base_y']
        tab_end_y = tray_height - drink_tab['height']
    else:
        # Slide up to top
        start_y = 0
        end_y = -tray_height
        tab_start_y = tray_height - drink_tab['height']
        tab_end_y = drink_tab['base_y']
    
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / duration, 1.0)
        
        current_y = start_y + (end_y - start_y) * progress
        drink_ui['tray_rect'].y = current_y
        
        # Update tab position to slide with tray
        tab_current_y = tab_start_y + (tab_end_y - tab_start_y) * progress
        drink_tab['rect'].y = tab_current_y
        
        # Update all related positions
        drink_ui['title_rect'].y = current_y + 40
        
        # Update dropdown positions to match new layout
        header_height = 80
        for dropdown in drink_ui['dropdowns']:
            if dropdown['pump_number'] <= 6:
                # Top row
                new_y = current_y + header_height + 40
                dropdown['rect'].y = new_y
                dropdown['label_rect'].y = new_y - 15
                # Update custom dropdown position
                dropdown['dropdown'].rect.y = new_y
            else:
                # Bottom row
                new_y = current_y + header_height + 40 + 120
                dropdown['rect'].y = new_y
                dropdown['label_rect'].y = new_y - 15
                # Update custom dropdown position
                dropdown['dropdown'].rect.y = new_y
        
        # Update generate button position
        drink_ui['generate_button_rect'].y = current_y + tray_height - 80
        drink_ui['generate_text_rect'].center = drink_ui['generate_button_rect'].center
        
        # Update tab layer
        remove_layer('drink_tab')
        add_layer(drink_tab['surface'], drink_tab['rect'], key='drink_tab')
        
        draw_drink_management_tray(drink_ui, True)
        draw_frame()
        
        if progress >= 1.0:
            break
        clock.tick(60)

def handle_drink_management_interaction(drink_ui, event, event_pos):
    """Handle interactions with drink management tray elements"""
    # Check if generate button is clicked
    if event.type == pygame.MOUSEBUTTONDOWN and drink_ui['generate_button_rect'].collidepoint(event_pos):
        return 'generate_menu'
    
    # Handle dropdown interactions
    for dropdown in drink_ui['dropdowns']:
        if dropdown['dropdown'].handle_event(event):
            # Check if selection changed
            new_value = dropdown['dropdown'].get_selected()
            if new_value != dropdown['current_value']:
                return f'dropdown_{dropdown["pump_number"]}_{new_value}'
    
    return None

def update_dropdown_selection(dropdown, new_value):
    """Update dropdown selection and save to config"""
    dropdown['current_value'] = new_value
    
    # Save to pump config
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except:
        config = {}
    
    config[f"Pump {dropdown['pump_number']}"] = new_value
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

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
    
    # Initialize drink management tray and tab
    drink_ui = create_drink_management_tray()
    drink_tab = create_drink_management_tab()
    drink_visible = False
    drink_tab_dragging = False
    drink_tab_drag_start_y = 0
    dropdown_open = None
    generating_menu = False
    
    # Add tabs to layers
    add_layer(settings_tab['surface'], settings_tab['rect'], key='settings_tab')
    add_layer(drink_tab['surface'], drink_tab['rect'], key='drink_tab')

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
            if drink_visible:
                for dropdown in drink_ui['dropdowns']:
                    if dropdown['dropdown'].handle_event(event):
                        # Check if selection changed
                        new_value = dropdown['dropdown'].get_selected()
                        if new_value != dropdown['current_value']:
                            update_dropdown_selection(dropdown, new_value)
            
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if drink management tab is clicked or dragged
                if drink_tab['rect'].collidepoint(event.pos):
                    drink_tab_dragging = True
                    drink_tab_drag_start_y = event.pos[1]
                    continue
                
                # Check if settings tab is clicked or dragged
                if settings_tab['rect'].collidepoint(event.pos):
                    tab_dragging = True
                    tab_drag_start_y = event.pos[1]
                    continue
                
                # Check if drink management tray is clicked
                if drink_visible and drink_ui['tray_rect'].collidepoint(event.pos):
                    interaction = handle_drink_management_interaction(drink_ui, event, event.pos)
                    if interaction == 'generate_menu':
                        generating_menu = True
                        # Start generation in a separate thread
                        import threading
                        def generate_thread():
                            global drink_ui, generating_menu
                            new_drinks = generate_new_drink_menu()
                            if new_drinks:
                                drink_ui = create_drink_management_tray()  # Refresh with new options
                                logger.info("Drink menu generated successfully")
                            else:
                                logger.error("Failed to generate new drink menu")
                            generating_menu = False
                        
                        thread = threading.Thread(target=generate_thread)
                        thread.start()
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
                
                # If drink management is visible and clicked outside, close it
                if drink_visible:
                    drink_visible = False
                    animate_drink_management_tray(drink_ui, drink_tab, drink_visible)
                    continue
                
                # If settings is visible and clicked outside, close it
                if settings_visible:
                    settings_visible = False
                    animate_settings_tray(settings_ui, settings_tab, settings_visible)
                    continue
                
                dragging = True
                drag_start_x = event.pos[0]
            if event.type == pygame.MOUSEMOTION:
                if drink_tab_dragging:
                    # Handle drink tab drag to open/close drink management
                    current_y = event.pos[1]
                    drag_distance = drink_tab_drag_start_y - current_y
                    
                    # If dragged down enough, open drink management
                    if drag_distance < -50 and not drink_visible:
                        drink_visible = True
                        animate_drink_management_tray(drink_ui, drink_tab, drink_visible)
                        drink_tab_dragging = False
                    # If dragged up enough, close drink management  
                    elif drag_distance > 30 and drink_visible:
                        drink_visible = False
                        animate_drink_management_tray(drink_ui, drink_tab, drink_visible)
                        drink_tab_dragging = False
                elif tab_dragging:
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
                if drink_tab_dragging:
                    # If drink tab was clicked without significant drag, toggle drink management
                    current_y = event.pos[1]
                    drag_distance = abs(drink_tab_drag_start_y - current_y)
                    if drag_distance < 10:  # Minimal movement, treat as click
                        drink_visible = not drink_visible
                        animate_drink_management_tray(drink_ui, drink_tab, drink_visible)
                    drink_tab_dragging = False
                    continue
                elif tab_dragging:
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
                            # Animate single logo click
                            if single_logo:
                                animate_logo_click(single_logo, single_rect, base_size=150, target_size=220, layer_key='single_logo', duration=150)

                            executor_watcher = make_drink(current_cocktail, 'single')

                            show_pouring_and_loading(watcher=executor_watcher)

                        elif double_rect.collidepoint(pos):
                            # Animate double logo click
                            if double_logo:
                                animate_logo_click(double_logo, double_rect, base_size=150, target_size=220, layer_key='double_logo', duration=150)

                            executor_watcher = make_drink(current_cocktail, 'double')

                            show_pouring_and_loading(executor_watcher)
                    
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
        if not drink_tab_dragging:
            if drink_visible:
                # Tab should be at the bottom of the tray
                drink_tab['rect'].y = drink_ui['tray_rect'].y + drink_ui['tray_rect'].height
            else:
                # Tab should be at the top
                drink_tab['rect'].y = drink_tab['base_y']
            
            # Update drink tab layer
            remove_layer('drink_tab')
            add_layer(drink_tab['surface'], drink_tab['rect'], key='drink_tab')
        
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
        
        # Draw drink management tray if visible
        if drink_visible:
            draw_drink_management_tray(drink_ui, True, events)
            
            # Handle custom dropdown selections
            for dropdown in drink_ui['dropdowns']:
                if dropdown['dropdown'].get_selected() != dropdown['current_value']:
                    new_value = dropdown['dropdown'].get_selected()
                    update_dropdown_selection(dropdown, new_value)
            
            # Show loading animation if generating
            if generating_menu:
                loading_font = pygame.font.SysFont(None, 24)
                loading_text = loading_font.render("Generating new drink menu...", True, (255, 255, 0))
                loading_rect = loading_text.get_rect(center=(screen_width // 2, drink_ui['tray_rect'].y + drink_ui['tray_rect'].height - 40))
                add_layer(loading_text, loading_rect, key='loading_text')
        
        # Draw settings tray if visible
        if settings_visible:
            draw_settings_tray(settings_ui, True)
        
        draw_frame()
        
        # Draw custom dropdowns AFTER draw_frame() so they appear on top
        if drink_visible:
            for dropdown in drink_ui['dropdowns']:
                # Debug: print dropdown info
                print(f"Drawing dropdown for Pump {dropdown['pump_number']}: {len(dropdown['dropdown'].options)} options")
                dropdown['dropdown'].draw(screen)
            pygame.display.flip()  # Update display after drawing dropdowns
        
        clock.tick(60)
    pygame.quit()

if __name__ == '__main__':
    run_interface()
