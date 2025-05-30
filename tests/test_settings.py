from io import StringIO
from dotenv import load_dotenv
import importlib


class TestSettings:
    """Test settings defaults and importing from env variables."""

    standard_config = {
        'DEBUG': 'true',
        'OPENAI_API_KEY': 'test token',
        'FULL_SCREEN': 'false',
        'OZ_COEFFICIENT': 10,
        'RETRACTION_TIME': 10,
        'USE_GPT_TRANSPARENCY': 'true',
        'COCKTAIL_IMAGE_SCALE': 0.75,
        'SHOW_RELOAD_COCKTAILS_BUTTON': 'true',
        'PUMP_CONCURRENCY': 2,
        'PUMP_CONFIG_FILE': 'test_pump_config.json',
        'COCKTAILS_FILE': 'test_cocktails.json',
        'LOGO_FOLDER': 'test_drink_logos',
        'INVERT_PUMP_PINS': 'true',
        'RELOAD_COCKTAILS_TIMEOUT': 3000
    }

    def get_settings(self, **config):
        """Get settings with manual env processing from a string"""
        config = StringIO('\n'.join([f'{key}={value}' for key, value in config.items()]))
        load_dotenv(stream=config, override=True)
        from .. import settings
        self.settings = importlib.reload(settings)

    def test_defaults(self):
        """Test default settings are set appropriately"""
        self.get_settings()
        
        assert self.settings.DEBUG == False
        assert self.settings.CONFIG_FILE == 'pump_config.json'
        assert self.settings.COCKTAILS_FILE == 'cocktails.json'
        assert self.settings.LOGO_FOLDER == 'drink_logos'
        assert self.settings.OPENAI_API_KEY == None
        assert self.settings.OZ_COEFFICIENT == 8.0
        assert self.settings.INVERT_PUMP_PINS == False
        assert self.settings.PUMP_CONCURRENCY == 3
        assert self.settings.FULL_SCREEN == True
        assert self.settings.SHOW_RELOAD_COCKTAILS_BUTTON == False
        assert self.settings.RELOAD_COCKTAILS_TIMEOUT == 0
        assert self.settings.RETRACTION_TIME == 0
        assert self.settings.USE_GPT_TRANSPARENCY == False
        assert self.settings.COCKTAIL_IMAGE_SCALE == 1.0

    def test_loading_settings(self):
        """Test that the env string values are loaded properly into settings"""
        self.get_settings(**self.standard_config)

        assert self.settings.DEBUG == True
        assert self.settings.CONFIG_FILE == 'test_pump_config.json'
        assert self.settings.COCKTAILS_FILE == 'test_cocktails.json'
        assert self.settings.LOGO_FOLDER == 'test_drink_logos'
        assert self.settings.OPENAI_API_KEY == 'test token'
        assert self.settings.OZ_COEFFICIENT == 10
        assert self.settings.INVERT_PUMP_PINS == True
        assert self.settings.PUMP_CONCURRENCY == 2
        assert self.settings.FULL_SCREEN == False
        assert self.settings.SHOW_RELOAD_COCKTAILS_BUTTON == True
        assert self.settings.RELOAD_COCKTAILS_TIMEOUT == 3000
        assert self.settings.RETRACTION_TIME == 10
        assert self.settings.USE_GPT_TRANSPARENCY == True
        assert self.settings.COCKTAIL_IMAGE_SCALE == 0.75

    def test_invalid_DEBUG(self):
        """Test that setting an invalid value as DEBUG fails silently and sets the value to 8.0"""
        self.get_settings(DEBUG='none')
        assert self.settings.DEBUG == False

    def test_invalid_OZ_COEFFICIENT(self):
        """Test that setting an invalid value as OZ_COEFFICIENT fails silently and sets the value to 8.0"""
        self.get_settings(OZ_COEFFICIENT='fortythree')
        assert self.settings.OZ_COEFFICIENT == 8.0

    def test_invalid_PUMP_CONCURRENCY(self):
        """Test that setting an invalid value for PUMP_CONCURRENCY fails silently and sets the value to 3"""
        self.get_settings(PUMP_CONCURRENCY='7.5')
        assert self.settings.PUMP_CONCURRENCY == 3

    def test_invalid_RELOAD_COCKTAILS_TIMEOUT(self):
        """Test that setting an invalid value for RELOAD_COCKTAILS_TIMEOUT fails silently and sets the value to 0"""
        self.get_settings(RELOAD_COCKTAILS_TIMEOUT='none')
        assert self.settings.RELOAD_COCKTAILS_TIMEOUT == 0

    def test_invalid_RETRACTION_TIME(self):
        """Test that setting an invalid value for RETRACTION_TIME fails silently and sets the value to 0"""
        self.get_settings(RETRACTION_TIME='none')
        assert self.settings.RETRACTION_TIME == 0

    def test_invalid_COCKTAIL_IMAGE_SCALE(self):
        """Test that setting an invalid value for COCKTAIL_IMAGE_SCALE fails silently and sets the value to 0"""
        self.get_settings(COCKTAIL_IMAGE_SCALE='none')
        assert self.settings.COCKTAIL_IMAGE_SCALE == 1

    def test_invalid_INVERT_PUMP_PINS(self):
        """Test that setting an invalid value for INVERT_PUMP_PINS fails silently and sets the value to 0"""
        self.get_settings(INVERT_PUMP_PINS='none')
        assert self.settings.INVERT_PUMP_PINS == False

    def test_invalid_FULL_SCREEN(self):
        """Test that setting an invalid value for FULL_SCREEN fails silently and sets the value to 0"""
        self.get_settings(FULL_SCREEN='none')
        assert self.settings.FULL_SCREEN == True

    def test_invalid_SHOW_RELOAD_COCKTAILS_BUTTON(self):
        """Test that setting an invalid value for SHOW_RELOAD_COCKTAILS_BUTTON fails silently and sets the value to 0"""
        self.get_settings(SHOW_RELOAD_COCKTAILS_BUTTON='none')
        assert self.settings.SHOW_RELOAD_COCKTAILS_BUTTON == False

    def test_invalid_USE_GPT_TRANSPARENCY(self):
        """Test that setting an invalid value for USE_GPT_TRANSPARENCY fails silently and sets the value to 0"""
        self.get_settings(USE_GPT_TRANSPARENCY='none')
        assert self.settings.USE_GPT_TRANSPARENCY == False
