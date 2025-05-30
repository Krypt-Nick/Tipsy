import base64
import os
import pygame
from dotenv import dotenv_values
import pytest


class TestHelpers:
    def get_helpers(self):
        """Get helpers from parent directory with default settings"""
        import sys
        sys.path.append('.')
        import helpers
        self.helpers = helpers

    def test_load_saved_config(self):
        """Test loading the pump config from a file"""
        self.get_helpers()
        saved_config = self.helpers.load_saved_config()
        assert saved_config != {}

    def test_save_config(self):
        """Test saving a new pump config to a file"""
        self.get_helpers()
        old_config = self.helpers.load_saved_config()
        try:
            test_config = {'Pump 1': 'Test Drink'}
            self.helpers.save_config(test_config)
            assert self.helpers.load_saved_config() == test_config
        finally:
            self.helpers.save_config(old_config)

    def test_load_cocktails(self):
        """Test loading cocktails from a file"""
        self.get_helpers()
        cocktails = self.helpers.load_cocktails()
        assert cocktails != {}

    def test_save_cocktails(self):
        """Test saving cocktails to a file, both with append, and replace"""
        self.get_helpers()
        old_cocktails = self.helpers.load_cocktails()
        try:
            cocktail_1 = {'normal_name': 'Test Cocktail 1'}
            cocktail_2 = {'normal_name': 'Test Cocktail 2'}
            self.helpers.save_cocktails({'cocktails': [cocktail_1]}, append=False)
            assert self.helpers.load_cocktails() == {'cocktails': [cocktail_1]}
            self.helpers.save_cocktails({'cocktails': [cocktail_2]}, append=True)
            assert self.helpers.load_cocktails() == {'cocktails': [cocktail_1, cocktail_2]}
        finally:
            self.helpers.save_cocktails(old_cocktails, append=False)

    def test_get_safe_name(self):
        """Test that cocktail name converts to file safe name"""
        self.get_helpers()
        safe_name = self.helpers.get_safe_name('This is a tEst name')
        assert safe_name == 'this_is_a_test_name.png'

    def test_get_cocktail_image_path(self):
        """Test getting an image path for a given cocktail"""
        self.get_helpers()
        cocktails = self.helpers.load_cocktails()
        path = self.helpers.get_cocktail_image_path(cocktails['cocktails'][0])
        assert path == 'drink_logos/vodka_cola.png'

    def test_get_valid_cocktails(self):
        """Test that only cocktails with images are loaded"""
        self.get_helpers()
        old_cocktails = self.helpers.load_cocktails()
        try:
            test_cocktails = {
                'cocktails': [old_cocktails['cocktails'][0], {'normal_name': 'NoImage'}]
            }
            self.helpers.save_cocktails(test_cocktails, False)
            valid_cocktails = self.helpers.get_valid_cocktails()
            assert valid_cocktails == [old_cocktails['cocktails'][0]]
        finally:
            self.helpers.save_cocktails(old_cocktails, False)

    def test_save_base64_image(self):
        """Test that b64 image saves and is reloadable"""
        self.get_helpers()
        img = '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'
        img_path = 'tests/test_image.png'
        output_path = self.helpers.save_base64_image(img, img_path)
        assert output_path == img_path
        with open(output_path, 'rb') as file:
            img_output = base64.b64encode(file.read()).decode("utf-8")
            assert img_output == img
        os.remove(output_path)

    def test_wrap_text(self):
        """Test that wrapping text returns a list of lines"""
        self.get_helpers()
        text = 'This is a 30 character string '
        pygame.init()
        font = pygame.font.SysFont(None, 12)
        lines = self.helpers.wrap_text(text, font, 50)
        assert lines == ['This is a 30', 'character', 'string']

    def test_get_image_prompt(self):
        """Test creation of the image generation prompt with and without ingredients"""
        self.get_helpers()
        cocktail_name = 'Test Cocktail'
        expected_prompt = (
            'A realistic illustration of a Test Cocktail cocktail on a plain white background. '
            'The lighting and shading create depth and realism, making the drink appear fresh and inviting. '
            'Do not include shadows, reflections, or the cocktail name in the image.'
        )
        prompt = self.helpers.get_image_prompt(cocktail_name)
        assert prompt == expected_prompt
        ingredients = ['Test ingredient 1', 'test ingredient 2', 'test Ingredient 3']
        ingredient_prompt = 'The cocktail ingredients are: Test ingredient 1, test ingredient 2, test Ingredient 3'
        prompt = self.helpers.get_image_prompt(cocktail_name, ingredients)
        assert prompt == f'{expected_prompt} {ingredient_prompt}'

    @pytest.mark.skipif('not config.getoption("--include-ai")', reason='Use the flag --include-ai to run OpenAI Tests')
    def test_generate_image(self):
        """Test using OpenAI to generate an image"""
        self.get_helpers()

        assert self.helpers.generate_image('Vodka Cola') == 'drink_logos/vodka_cola.png'

        config = dotenv_values(".env")
        assert 'OPENAI_API_KEY' in config, 'OPENAI_API_KEY not found in .env file. Please add a API key to run AI tests.'

        image_path = self.helpers.generate_image('Test Cocktail', ingredients=['Test Ingredient'], api_key=config['OPENAI_API_KEY'])
        assert os.path.exists(image_path)
        os.remove(image_path)

        image_path = self.helpers.generate_image('Test Transparent Cocktail', ingredients=['Test Transparent Ingredient'], api_key=config['OPENAI_API_KEY'], use_gpt_transparency=True)
        assert os.path.exists(image_path)
        os.remove(image_path)

