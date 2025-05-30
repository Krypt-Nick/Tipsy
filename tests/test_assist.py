from openai import OpenAI, OpenAIError
import pytest
import logging
from dotenv import dotenv_values


logger = logging.getLogger(__name__)


class TestAssist:
    def get_assist(self):
        """Get assist module from parent directory with default settings"""
        import sys
        sys.path.append('.')
        import assist
        self.assist = assist
        import helpers
        self.helpers = helpers

    def test_get_client(self):
        """Test getting the OpenAI Client"""
        self.get_assist()
        with pytest.raises(OpenAIError):
            self.assist.get_client()
        
        test_api_key = 'test_api_key'
        client = self.assist.get_client(api_key=test_api_key)
        assert isinstance(client, OpenAI)
        assert client.api_key == test_api_key

    @pytest.mark.skipif('not config.getoption("--include-ai")', reason='Use the flag --include-ai to run OpenAI Tests')
    def test_generate_cocktails(self):
        """Test generation of cocktails using OpenAI"""
        self.get_assist()

        config = dotenv_values(".env")
        assert 'OPENAI_API_KEY' in config, 'OPENAI_API_KEY not found in .env file. Please add a API key to run AI tests.'

        pumps = self.helpers.load_saved_config()
        cocktails = self.assist.generate_cocktails(pumps, api_key=config['OPENAI_API_KEY'])
        assert 'cocktails' in cocktails
        assert len(cocktails['cocktails']) > 0
        
        for cocktail in cocktails['cocktails']:
            logger.info(f'Checking returned cocktail: {cocktail}')
            assert 'normal_name' in cocktail
            assert len(cocktail['normal_name']) > 0
            assert 'ingredients' in cocktail
            assert len(cocktail['ingredients']) > 0
            for ingredient, amount in cocktail['ingredients'].items():
                assert len(ingredient) > 0
                assert len(amount) > 0

        
