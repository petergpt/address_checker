import os
import json
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

class OpenAIProcessor:
    def __init__(self):
        # Initialize the OpenAI client instance with API key from environment
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.prompts = self.load_prompts('prompts/prompts.json')

    def load_prompts(self, file_path):
        """Load the prompts from a JSON file."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: Prompt file {file_path} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Failed to decode the JSON file {file_path}.")
            return {}

    def get_prompt(self, prompt_type, version):
        """Get a specific version of a prompt."""
        try:
            return self.prompts[prompt_type][version]
        except KeyError:
            print(f"Error: Prompt version '{version}' for '{prompt_type}' not found.")
            return ""

    def process_single_address(self, address, prompt_type, version):
        """
        Process a single address with OpenAI.
        """
        prompt = self.get_prompt(prompt_type, version)
        if not prompt:
            return {}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": address}
                ],
                temperature=1,
                max_tokens=4095,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "address_schema",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "FirstName": {"type": "string", "description": "First name of the recipient."},
                                "LastName": {"type": "string", "description": "Last name of the recipient."},
                                "StreetName": {"type": "string", "description": "Name of the street and house number."},
                                "Town": {"type": "string", "description": "Name of the town or city."},
                                "Postcode": {"type": "string", "description": "The postal code."},
                                "Country": {"type": "string", "description": "Country code, e.g., 'GB'."}
                            },
                            "required": ["FirstName", "LastName", "StreetName", "Town", "Postcode", "Country"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            response_content = response.choices[0].message.content
            return json.loads(response_content)  # Convert from JSON string to Python dictionary
        except Exception as e:
            print(f"Error processing address with OpenAI: {str(e)}")
            return {}

    def process_addresses_parallel(self, addresses, prompt_type, version):
        """
        Process multiple addresses in parallel using the OpenAI API.
        """
        results = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.process_single_address, address, prompt_type, version): address for address in addresses}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error in parallel processing: {str(e)}")
        return results

    def separate_addresses(self, addresses, version="v1"):
        """Process addresses for separation (Step 1, expect plain text)."""
        # Adjust to use a single API call since this is for separating addresses
        prompt = self.get_prompt('separate_addresses', version)
        if not prompt:
            return []

        # Properly format addresses as one string
        address_content = "\n".join(addresses)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": address_content}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            return self.clean_text_response(response.choices[0].message.content)
        except Exception as e:
            print(f"Error processing addresses with OpenAI: {str(e)}")
            return []

    def format_addresses(self, separated_addresses, version="v1"):
        """Process separated addresses for formatting (Step 2, expect structured output)."""
        return self.process_addresses_parallel(separated_addresses, 'format_addresses', version)

    def clean_text_response(self, response_content):
        """Clean up the response to remove extra newlines and whitespace for Step 1."""
        cleaned_lines = response_content.split("\n")
        cleaned_addresses = [line.strip() for line in cleaned_lines if line.strip()]
        return cleaned_addresses
