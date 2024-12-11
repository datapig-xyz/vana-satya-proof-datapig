import json
import logging
import os
from typing import Dict, Any

import requests

from my_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])


    def generate(self) -> ProofResponse:
        logging.info("Starting proof generation")
        total_score = 0
        score_threshold = 0.2

        for input_filename in os.listdir(self.config['input_dir']):
            input_file = os.path.join(self.config['input_dir'], input_filename)
            # if os.path.splitext(input_file)[1].lower() == '.json':
            #     total_score = 1
            try:
                with open(input_file, 'r') as f:
                    json_data = json.load(f)
                
                # Validate JSON structure
                if not all(key in json_data for key in ['address', 'unixtime', 'preferences']):
                    logging.error(f"Missing required keys in JSON file {input_file}")
                    total_score = 0
                    continue
                
                if not all(key in json_data['preferences'] for key in ['categories', 'likes']):
                    logging.error(f"Missing required preference keys in JSON file {input_file}")
                    total_score = 0
                    continue
                
                # Validate data types
                if not isinstance(json_data['address'], str) or \
                not isinstance(json_data['unixtime'], int) or \
                not isinstance(json_data['preferences']['categories'], list) or \
                not isinstance(json_data['preferences']['likes'], dict):
                    logging.error(f"Invalid data types in JSON file {input_file}")
                    total_score = 0
                    continue
                
                # If all validations pass, set score to 1
                total_score = 1
                
            except (json.JSONDecodeError, IOError, KeyError) as e:
                logging.error(f"Error processing JSON file {input_file}: {e}")
                total_score = 0

        # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = total_score  # Does the data belong to the user? Or is it fraudulent?
        self.proof_response.quality = total_score  # How high quality is the data?
        self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        self.proof_response.uniqueness = 0  # How unique is the data relative to other datasets? (Not implemented here)

        # Calculate overall score and validity
        self.proof_response.score = 0.6 * self.proof_response.quality + 0.4 * self.proof_response.ownership
        self.proof_response.valid = total_score >= score_threshold

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {
            'total_score': total_score,
            'score_threshold': score_threshold,
        }

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response


def fetch_random_number() -> float:
    """Demonstrate HTTP requests by fetching a random number from random.org."""
    try:
        response = requests.get('https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new')
        return float(response.text.strip())
    except requests.RequestException as e:
        logging.warning(f"Error fetching random number: {e}. Using local random.")
        return __import__('random').random()
