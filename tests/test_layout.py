import os
import sys
import pygame
import pytest

# Ensure project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import get_centered_rect_for_surface


def test_centered_rect_is_middle_of_screen():
    pygame.init()
    try:
        screen_width, screen_height = 700, 700
        # Create a dummy surface representing a scaled cocktail image (e.g., 350x350)
        image = pygame.Surface((350, 350), pygame.SRCALPHA)
        rect = get_centered_rect_for_surface(image, screen_width, screen_height)
        # The rect center should match screen center
        assert rect.center == (screen_width // 2, screen_height // 2)

        # With offsets, center should shift accordingly
        rect2 = get_centered_rect_for_surface(image, screen_width, screen_height, offset_x=50, offset_y=-20)
        assert rect2.center == (screen_width // 2 + 50, screen_height // 2 - 20)
    finally:
        pygame.quit() 